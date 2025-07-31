import { useState, FormEvent, forwardRef, useImperativeHandle, useRef } from 'react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export interface MessageInputHandle {
  focus: () => void;
  setValue: (value: string) => void;
  appendValue: (value: string) => void;
  showInterimText: (text: string) => void;
  clearInterimText: () => void;
}

const MessageInput = forwardRef<MessageInputHandle, MessageInputProps>(
  ({ onSendMessage, disabled = false }, ref) => {
    const [message, setMessage] = useState('');
    const [interimText, setInterimText] = useState('');
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => {
        inputRef.current?.focus();
      },
      setValue: (value: string) => {
        setMessage(value);
      },
      appendValue: (value: string) => {
        setMessage(prev => {
          // Don't add duplicate text or fragments that are already included
          const trimmedValue = value.trim();
          const trimmedPrev = prev.trim();
          
          // If the new value is empty, return previous
          if (!trimmedValue) return prev;
          
          // If previous is empty, use new value
          if (!trimmedPrev) return trimmedValue;
          
          // Check if new value is already contained in previous text (avoid duplicates)
          if (trimmedPrev.includes(trimmedValue)) {
            return prev; // Don't add if already present
          }
          
          // Check if previous text ends with the beginning of new value (avoid fragments)
          const words = trimmedPrev.split(' ');
          const lastWord = words[words.length - 1];
          
          // If new value starts with the last word, replace the last word instead of appending
          if (trimmedValue.toLowerCase().startsWith(lastWord.toLowerCase()) && lastWord.length < trimmedValue.length) {
            const withoutLastWord = words.slice(0, -1).join(' ');
            return withoutLastWord ? `${withoutLastWord} ${trimmedValue}` : trimmedValue;
          }
          
          // Otherwise append normally
          return `${prev} ${trimmedValue}`;
        });
        setInterimText(''); // Clear interim text when final text is added
      },
      showInterimText: (text: string) => {
        setInterimText(text);
      },
      clearInterimText: () => {
        setInterimText('');
      }
    }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      setInterimText(''); // Clear interim text when sending message
    }
  };

  const displayValue = interimText ? `${message}${message ? ' ' : ''}${interimText}` : message;

  return (
    <form onSubmit={handleSubmit} className="message-input-form">
      <div className="input-container">
        <textarea
          ref={inputRef}
          value={displayValue}
          onChange={(e) => {
            // When user manually edits, clear interim text and update message
            const newValue = e.target.value;
            setInterimText('');
            setMessage(newValue);
          }}
          onKeyDown={(e) => {
            // Submit on Enter (but not Shift+Enter for multi-line)
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e as any);
            }
          }}
          placeholder="Type your message..."
          disabled={disabled}
          className="message-input"
          rows={3}
          style={{
            color: interimText ? '#666' : 'inherit',
            resize: 'vertical',
            minHeight: '60px'
          }}
        />
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="send-button"
        >
          Send
        </button>
      </div>
      {interimText && (
        <div className="interim-preview" style={{
          fontSize: '0.8em',
          color: '#888',
          fontStyle: 'italic',
          marginTop: '4px'
        }}>
          Real-time: {interimText}
        </div>
      )}
    </form>
  );
});

MessageInput.displayName = 'MessageInput';

export default MessageInput;