import { useState, useCallback, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import ChatPanel from './ChatPanel';
import AuthForm from './AuthForm';
import { useAuth } from '../contexts/AuthContext';
import styles from './ChatWidget.module.css';


function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasUnread, setHasUnread] = useState(false);
  

  const { user, token, isAuthenticated, login, register, logout } = useAuth();
  const [authMode, setAuthMode] = useState(null); // 'login' | 'register' | null
  const [authError, setAuthError] = useState(null);

  
  const loadChatHistory = useCallback(async (authToken) => {
    try {
      const response = await fetch('/api/history', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const historyMessages = data.messages.map((msg) => ({
          text: msg.message,
          isBot: msg.is_bot,
        }));
        setMessages(historyMessages);
      }
    } catch {
      // Ignore history load errors
    }
  }, []);

  
  useEffect(() => {
    if (isAuthenticated && token) {
      loadChatHistory(token);
    }
  }, [isAuthenticated, token, loadChatHistory]);

  
  useEffect(() => {
    if (!isAuthenticated) {
      setMessages([]);
    }
  }, [isAuthenticated]);

  // Toggle chat panel open/closed
  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
    if (!isOpen) {
      setHasUnread(false);
    }
  }, [isOpen]);

  // Close chat panel
  const handleClose = useCallback(() => {
    setIsOpen(false);
    setAuthMode(null);
  }, []);

  // Send message to API
  const handleSend = useCallback(async (text) => {
    // Add user message to chat
    const userMessage = { text, isBot: false };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      // Add bot response to chat
      const botMessage = { text: data.response, isBot: true };
      setMessages((prev) => [...prev, botMessage]);
      
      // Set unread if panel is closed
      if (!isOpen) {
        setHasUnread(true);
      }
    } catch {
      setError('Unable to connect. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [isOpen, token]);

  // Auth handlers
  const handleLogin = useCallback(() => {
    setAuthMode('login');
    setAuthError(null);
  }, []);

  const handleRegister = useCallback(() => {
    setAuthMode('register');
    setAuthError(null);
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
    // Messages are cleared via the useEffect watching isAuthenticated
  }, [logout]);

  const handleAuthSubmit = useCallback(async (formData) => {
    setAuthError(null);
    
    try {
      if (authMode === 'login') {
        await login(formData.email, formData.password);
      } else {
        await register(formData.name, formData.email, formData.password);
      }
      setAuthMode(null);
      // Chat history is loaded via the useEffect watching isAuthenticated
    } catch (error) {
      setAuthError(error.message);
    }
  }, [authMode, login, register]);

  const handleAuthCancel = useCallback(() => {
    setAuthMode(null);
    setAuthError(null);
  }, []);

  return (
    <div className={styles.widget}>
      {isOpen ? (
        authMode ? (
          <AuthForm
            mode={authMode}
            onSubmit={handleAuthSubmit}
            onCancel={handleAuthCancel}
            error={authError}
          />
        ) : (
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            onClose={handleClose}
            isLoading={isLoading}
            error={error}
            user={user}
            onLogin={handleLogin}
            onRegister={handleRegister}
            onLogout={handleLogout}
          />
        )
      ) : (
        <ChatBubble onClick={handleToggle} hasUnread={hasUnread} />
      )}
    </div>
  );
}

export default ChatWidget;
