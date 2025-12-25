# Design Document: React Chatbot Frontend

## Overview

This design creates a React-based frontend with a floating AI Chatbot Widget positioned in the bottom-left corner of the website. The system includes user authentication, role-based access control, and personalized chat experiences. The frontend communicates with the existing Flask backend API and extends the PostgreSQL database with a users table.

The solution uses:
- **React 18**: Frontend framework with hooks
- **Vite**: Build tool and dev server
- **CSS Modules**: Scoped styling for components
- **JWT**: JSON Web Tokens for session management
- **bcrypt**: Password hashing (backend)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Main Website                        │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │           ChatWidget (Fixed Position)            │ │  │
│  │  │  ┌─────────┐  ┌──────────────────────────────┐  │ │  │
│  │  │  │ Bubble  │  │      Chat Panel              │  │ │  │
│  │  │  │  Icon   │  │  ┌────────────────────────┐  │  │ │  │
│  │  │  └─────────┘  │  │    Header (User/Auth)  │  │  │ │  │
│  │  │               │  ├────────────────────────┤  │  │ │  │
│  │  │               │  │    Message List        │  │  │ │  │
│  │  │               │  ├────────────────────────┤  │  │ │  │
│  │  │               │  │    Input Area          │  │  │ │  │
│  │  │               │  └────────────────────────┘  │  │ │  │
│  │  │               └──────────────────────────────┘  │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (REST API)
┌────────────────────────▼────────────────────────────────────┐
│                    Flask Backend API                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  /api/chat   │  │  /api/auth   │  │ /api/history │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  users   │ │ messages │ │ products │ │  orders  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Frontend Components

#### ChatWidget (`frontend/src/components/ChatWidget.jsx`)
Main container component managing widget state.

```javascript
// Props: none (uses context for auth)
// State: isOpen, messages, isLoading, error

function ChatWidget() {
  // Toggle between bubble and expanded panel
  // Manage message sending and receiving
  // Handle authentication state
}
```

#### ChatBubble (`frontend/src/components/ChatBubble.jsx`)
Floating button that opens the chat panel.

```javascript
// Props: onClick, hasUnread
function ChatBubble({ onClick, hasUnread }) {
  // Render floating button with chat icon
  // Show notification badge if hasUnread
}
```

#### ChatPanel (`frontend/src/components/ChatPanel.jsx`)
Expanded chat interface panel.

```javascript
// Props: messages, onSend, onClose, isLoading, user
function ChatPanel({ messages, onSend, onClose, isLoading, user }) {
  // Render header with user info or auth buttons
  // Render message list
  // Render input area
}
```

#### AuthForm (`frontend/src/components/AuthForm.jsx`)
Login and registration forms.

```javascript
// Props: mode ('login' | 'register'), onSubmit, onCancel, error
function AuthForm({ mode, onSubmit, onCancel, error }) {
  // Render appropriate form fields
  // Handle form submission
}
```

### 2. Backend API Extensions

#### Auth Endpoints (`src/api.py`)

```python
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with email, password, name"""
    
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Invalidate user session"""
    
@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user info"""
```

#### Chat History Endpoints

```python
@app.route('/api/history', methods=['GET'])
def get_chat_history():
    """Get chat history for authenticated user"""
    
# Modified /api/chat to store messages for authenticated users
```

### 3. Database Layer Extensions

```python
# User management methods in Database class
def create_user(self, email, password_hash, name, role='customer'):
    """Insert new user record"""
    
def get_user_by_email(self, email):
    """Query user by email"""
    
def update_last_login(self, user_id):
    """Update last_login timestamp"""
    
def save_chat_message(self, user_id, message, is_bot):
    """Store chat message"""
    
def get_chat_history(self, user_id, limit=50):
    """Retrieve user's chat history"""
```

## Data Models

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-increment user ID |
| email | VARCHAR(255) UNIQUE | User email address |
| password_hash | VARCHAR(255) | bcrypt hashed password |
| name | VARCHAR(100) | User display name |
| role | VARCHAR(20) | Role: guest, customer, admin |
| created_at | TIMESTAMP | Account creation time |
| last_login | TIMESTAMP | Last login timestamp |

### Chat Messages Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-increment message ID |
| user_id | INTEGER | Foreign key to users |
| message | TEXT | Message content |
| is_bot | BOOLEAN | True if bot response |
| created_at | TIMESTAMP | Message timestamp |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Chat API response format
*For any* valid message string sent to /api/chat, the response SHALL be valid JSON containing a "response" field with a non-empty string.
**Validates: Requirements 2.1**

### Property 2: User message display
*For any* message sent by the user, it SHALL appear in the chat history array before the corresponding bot response.
**Validates: Requirements 2.2, 2.3**

### Property 3: Password hashing
*For any* user registration, the stored password_hash SHALL NOT equal the plaintext password and SHALL be a valid bcrypt hash.
**Validates: Requirements 3.2**

### Property 4: Login timestamp update
*For any* successful login, the user's last_login timestamp SHALL be greater than or equal to the timestamp before the login attempt.
**Validates: Requirements 3.3**

### Property 5: Authentication token validity
*For any* valid email/password combination, authentication SHALL return a JWT token that can be decoded to reveal the user's id and role.
**Validates: Requirements 4.3**

### Property 6: Generic error messages
*For any* failed authentication attempt, the error message SHALL NOT indicate whether the email exists in the system.
**Validates: Requirements 4.4**

### Property 7: Default role assignment
*For any* new user registration, the assigned role SHALL be 'customer' unless explicitly specified otherwise.
**Validates: Requirements 5.1**

### Property 8: Chat history persistence
*For any* message sent by an authenticated user, querying their chat history SHALL include that message.
**Validates: Requirements 6.1, 6.2**

## Error Handling

| Error Scenario | Handling |
|----------------|----------|
| API connection failure | Display "Unable to connect" message, allow retry |
| Invalid credentials | Display generic "Invalid email or password" |
| Token expired | Redirect to login, clear local storage |
| Empty message | Prevent submission, show validation hint |
| Server error (500) | Display "Something went wrong" with retry option |

## Testing Strategy

### Unit Tests
- Test React components render correctly
- Test form validation logic
- Test API service functions
- Test authentication state management

### Property-Based Testing
Using **fast-check** library for JavaScript property-based testing.

Each property test will:
1. Generate random valid inputs
2. Execute the operation
3. Verify the property holds

Property tests will be annotated with:
```javascript
// **Feature: react-chatbot-frontend, Property {number}: {property_text}**
```

Configuration: Minimum 100 iterations per property test.

### Integration Tests
- Test full authentication flow
- Test chat message round-trip
- Test role-based access restrictions

