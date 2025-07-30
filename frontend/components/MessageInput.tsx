import { useState, FormEvent, forwardRef, useImperativeHandle, useRef } from 'react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export interface MessageInputHandle {
  focus: () => void;
  setValue: (value: string) => void;
  appendValue: (value: string) => void;
}

const MessageInput = forwardRef<MessageInputHandle, MessageInputProps>(
  ({ onSendMessage, disabled = false }, ref) => {
    const [message, setMessage] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => {
        inputRef.current?.focus();
      },
      setValue: (value: string) => {
        setMessage(value);
      },
      appendValue: (value: string) => {
        setMessage(prev => prev ? `${prev} ${value}` : value);
      }
    }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="message-input-form">
      <div className="input-container">
        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          disabled={disabled}
          className="message-input"
        />
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="send-button"
        >
          Send
        </button>
      </div>
    </form>
  );
});

MessageInput.displayName = 'MessageInput';

export default MessageInput;