import styles from './ChatBubble.module.css';

/**
 * ChatBubble Component
 * Floating button that opens the chat panel
 * Requirements: 1.1, 1.2
 */
function ChatBubble({ onClick, hasUnread }) {
  return (
    <button
      className={styles.bubble}
      onClick={onClick}
      aria-label={hasUnread ? 'Open chat - new messages' : 'Open chat'}
      type="button"
    >
      {/* Chat Icon */}
      <svg
        className={styles.icon}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      
      {/* Notification Badge */}
      {hasUnread && (
        <span className={styles.badge} aria-label="Unread messages">
          !
        </span>
      )}
    </button>
  );
}

export default ChatBubble;
