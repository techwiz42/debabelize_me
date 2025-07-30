import openai
import json
from typing import Optional
from app.core.config import settings
from app.services.session_service import session_service
from app.services.search_service import search_service
from app.services.voice_service import voice_service
from app.models.schemas import ChatMessage, ChatResponse

# Initialize OpenAI
openai.api_key = settings.openai_api_key

class ChatService:
    def __init__(self):
        self.language_names = {
            'af': 'Afrikaans', 'sq': 'Albanian', 'ar': 'Arabic', 'az': 'Azerbaijani',
            'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bs': 'Bosnian',
            'bg': 'Bulgarian', 'ca': 'Catalan', 'zh': 'Chinese', 'hr': 'Croatian',
            'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
            'et': 'Estonian', 'fi': 'Finnish', 'fr': 'French', 'gl': 'Galician',
            'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'he': 'Hebrew',
            'hi': 'Hindi', 'hu': 'Hungarian', 'id': 'Indonesian', 'it': 'Italian',
            'ja': 'Japanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'ko': 'Korean',
            'lv': 'Latvian', 'lt': 'Lithuanian', 'mk': 'Macedonian', 'ms': 'Malay',
            'ml': 'Malayalam', 'mr': 'Marathi', 'no': 'Norwegian', 'fa': 'Persian',
            'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian',
            'ru': 'Russian', 'sr': 'Serbian', 'sk': 'Slovak', 'sl': 'Slovenian',
            'es': 'Spanish', 'sw': 'Swahili', 'sv': 'Swedish', 'tl': 'Tagalog',
            'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish',
            'uk': 'Ukrainian', 'ur': 'Urdu', 'vi': 'Vietnamese', 'cy': 'Welsh'
        }
    
    def _get_system_prompt(self, language: Optional[str] = None) -> str:
        """Generate system prompt with optional language specification"""
        base_prompt = """You are Babs, a friendly and witty AI assistant with a good sense of humor. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational and don't be afraid to be a bit cheeky when the moment calls for it. You're like that friend who gives good advice but might also roast you a little."""
        
        if language and language != 'auto' and language != 'en':
            language_name = self.language_names.get(language, language)
            return f"""You are Babs, a friendly and witty AI assistant with a good sense of humor. Always respond in {language_name}. You're helpful but not overly eager - sometimes a little sass or a joke is more appropriate than a lengthy explanation. Keep responses conversational in {language_name} and don't be afraid to be a bit cheeky when the moment calls for it."""
        
        return base_prompt
    
    async def process_chat_message(self, message: ChatMessage) -> ChatResponse:
        """Process a chat message and return response"""
        # Get or create session
        session_id = session_service.get_or_create_session(message.session_id)
        conversation_history = session_service.get_session_conversation_history(session_id)
        
        # Add to session-specific conversation history
        conversation_history.append({"role": "user", "content": message.message})
        
        # Prepare messages for GPT
        system_prompt = self._get_system_prompt(message.language)
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history
        ]
        
        # Stream response from GPT with function calling
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            tools=search_service.search_tools,
            stream=False
        )
        
        # Handle function calls
        if response.choices[0].message.tool_calls:
            # Add the assistant's message with tool calls to conversation
            conversation_history.append({
                "role": "assistant", 
                "content": response.choices[0].message.content, 
                "tool_calls": response.choices[0].message.tool_calls
            })
            
            # Execute function calls
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.function.name == "web_search":
                    function_args = json.loads(tool_call.function.arguments)
                    search_result = await search_service.web_search(function_args["query"])
                    
                    # Add function result to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": search_result,
                        "tool_call_id": tool_call.id
                    })
            
            # Get final response with function results
            final_messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history[1:]  # Skip the old system message if any
            ]
            final_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=final_messages,
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            ai_response = final_response.choices[0].message.content
        else:
            ai_response = response.choices[0].message.content
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Determine response language
        response_language = message.language if message.language else "en"
        
        return ChatResponse(
            response=ai_response,
            debabelized_text=message.message,
            response_language=response_language,
            session_id=session_id
        )
    
    async def process_streaming_chat(self, websocket, data: dict):
        """Process streaming chat for WebSocket"""
        message = data.get("message", "")
        language = data.get("language")
        session_id_input = data.get("session_id")
        
        # Get or create session
        session_id = session_service.get_or_create_session(session_id_input)
        conversation_history = session_service.get_session_conversation_history(session_id)
        
        # Add to session-specific conversation history
        conversation_history.append({"role": "user", "content": message})
        
        # Prepare messages for GPT
        system_prompt = self._get_system_prompt(language)
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history
        ]
        
        # First try with function calling (non-streaming to handle tools)
        initial_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            tools=search_service.search_tools,
            stream=False
        )
        
        # Handle function calls if any
        if initial_response.choices[0].message.tool_calls:
            # Add the assistant's message with tool calls to conversation
            conversation_history.append({
                "role": "assistant", 
                "content": initial_response.choices[0].message.content, 
                "tool_calls": initial_response.choices[0].message.tool_calls
            })
            
            # Execute function calls
            for tool_call in initial_response.choices[0].message.tool_calls:
                if tool_call.function.name == "web_search":
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Notify client that we're searching
                    await websocket.send_json({
                        "type": "content",
                        "content": f"🔍 Searching for: {function_args['query']}...\n\n"
                    })
                    
                    search_result = await search_service.web_search(function_args["query"])
                    
                    # Add function result to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": search_result,
                        "tool_call_id": tool_call.id
                    })
            
            # Get final response with function results (streaming)
            final_messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history[1:]  # Skip the old system message if any
            ]
            final_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=final_messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            full_response = ""
            for chunk in final_response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    await websocket.send_json({
                        "type": "content",
                        "content": content,
                        "session_id": session_id
                    })
        else:
            # No function calls, stream normally
            stream_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            full_response = ""
            for chunk in stream_response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    await websocket.send_json({
                        "type": "content",
                        "content": content,
                        "session_id": session_id
                    })
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": full_response})
        
        # Send completion signal
        await websocket.send_json({
            "type": "complete",
            "full_response": full_response,
            "session_id": session_id
        })

# Global chat service instance
chat_service = ChatService()