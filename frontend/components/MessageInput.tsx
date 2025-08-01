import { useState, FormEvent, forwardRef, useImperativeHandle, useRef, useEffect } from 'react';

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

    useEffect(() => {
      console.log('Message state changed:', message, 'Length:', message.length, 'Trimmed:', message.trim(), 'Send button disabled:', disabled || !message.trim());
    }, [message, disabled]);

    useImperativeHandle(ref, () => ({
      focus: () => {
        inputRef.current?.focus();
      },
      setValue: (value: string) => {
        console.log('setValue called with:', value);
        setMessage(value);
      },
      appendValue: (value: string) => {
        console.log('appendValue called with:', value);
        setMessage(prev => {
          console.log('Previous message state:', prev);
          const trimmedValue = value.trim();
          const trimmedPrev = prev.trim();
          
          // If the new value is empty, return previous
          if (!trimmedValue) return prev;
          
          // If previous is empty, use new value
          if (!trimmedPrev) return trimmedValue;
          
          // Enhanced duplicate detection: check exact match, containment, and similarity
          const lowerValue = trimmedValue.toLowerCase();
          const lowerPrev = trimmedPrev.toLowerCase();
          
          // Skip if exact match or already fully contained
          if (lowerPrev === lowerValue || lowerPrev.includes(lowerValue)) {
            console.log('Skipping duplicate/contained text:', trimmedValue);
            return prev;
          }
          
          // Check for substantial overlap (>70% of words)
          const valueWords = lowerValue.split(' ');
          const prevWords = lowerPrev.split(' ');
          const matchingWords = valueWords.filter(word => prevWords.includes(word));
          const overlapRatio = matchingWords.length / valueWords.length;
          
          if (overlapRatio > 0.7) {
            console.log('Skipping high-overlap text:', trimmedValue, 'overlap:', overlapRatio);
            return prev;
          }
          
          // Check if new value extends the last sentence naturally
          const lastSentence = trimmedPrev.split(/[.!?]/).pop()?.trim() || '';
          if (lastSentence && lowerValue.startsWith(lastSentence.toLowerCase())) {
            // Replace the incomplete last sentence with the complete one
            const beforeLastSentence = trimmedPrev.substring(0, trimmedPrev.lastIndexOf(lastSentence));
            console.log('Replacing incomplete sentence:', lastSentence, 'with:', trimmedValue);
            return beforeLastSentence ? `${beforeLastSentence}${trimmedValue}` : trimmedValue;
          }
          
          // Normal append with proper spacing
          const needsSpace = trimmedPrev && !trimmedPrev.endsWith(' ') && !trimmedValue.startsWith(' ');
          const result = needsSpace ? `${trimmedPrev} ${trimmedValue}` : `${trimmedPrev}${trimmedValue}`;
          console.log('Appending text normally:', trimmedValue);
          console.log('Final result:', result);
          return result;
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
          onClick={() => console.log('Send button clicked, disabled:', disabled, 'message:', message, 'trimmed empty:', !message.trim())}
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