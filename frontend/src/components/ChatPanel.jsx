import { useState, useRef, useEffect } from 'react';
import styles from './ChatPanel.module.css';

/**
 * ChatPanel Component
 * Expanded chat interface panel
 * Requirements: 1.2, 1.3, 2.2, 2.3, 2.4
 */
function ChatPanel({
  messages,
  onSend,
  onClose,
  isLoading,
  error,
  user,
  onLogin,
  onRegister,
  onLogout,
}) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !isLoading) {
      onSend(trimmedValue);
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={styles.panel} role="dialog" aria-label="Chat panel">
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInfo}>
          <div>
            <div className={styles.headerTitle}>E-Shop Support</div>
            <div className={styles.headerSubtitle}>
              {user ? `Welcome, ${user.name}` : 'How can we help?'}
            </div>
          </div>
        </div>
        <div className={styles.headerActions}>
          {user ? (
            <div className={styles.userInfo}>
              <span className={styles.userName}>{user.name}</span>
              <button
                className={styles.logoutButton}
                onClick={onLogout}
                type="button"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className={styles.authButtons}>
              <button
                className={`${styles.authButton} ${styles.loginButton}`}
                onClick={onLogin}
                type="button"
              >
                Login
              </button>
              <button
                className={`${styles.authButton} ${styles.registerButton}`}
                onClick={onRegister}
                type="button"
              >
                Register
              </button>
            </div>
          )}
          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close chat"
            type="button"
          >
            <svg
              className={styles.closeIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </header>

      {/* Messages Area */}
      <div className={styles.messages} role="log" aria-live="polite">
        {messages.length === 0 && !isLoading && !error ? (
          <div className={styles.emptyState}>
            <svg
              className={styles.emptyIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <div className={styles.emptyTitle}>Start a conversation</div>
            <div className={styles.emptyText}>
              Ask us anything about your orders, products, or policies.
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`${styles.message} ${
                  msg.isBot ? styles.botMessage : styles.userMessage
                }`}
              >
                {msg.text}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className={styles.loadingMessage}>
                <div className={styles.loadingDots}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            
            {/* Error Message */}
            {error && (
              <div className={styles.errorMessage}>
                {error}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <form className={styles.inputArea} onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className={styles.input}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isLoading}
          aria-label="Chat message input"
        />
        <button
          type="submit"
          className={styles.sendButton}
          disabled={!inputValue.trim() || isLoading}
          aria-label="Send message"
        >
          <svg
            className={styles.sendIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
