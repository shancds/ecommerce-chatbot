# Requirements Document

## Introduction

This specification defines the requirements for a React-based frontend that provides an AI Chatbot Widget for the E-Shop Customer Support system. The widget appears as a chat bubble in the bottom-left corner of the website and provides a personalized chat experience based on user authentication and role-based access control. The system includes user management with database storage to enable personalized interactions.

## Glossary

- **Chatbot_Widget**: The React component that displays as a floating chat bubble and expands into a chat interface
- **User_System**: The authentication and user management module that handles login, registration, and session management
- **Role_Control**: The access control system that determines user permissions (guest, customer, admin)
- **Chat_API**: The backend REST API endpoint that processes chat messages
- **User_Table**: The PostgreSQL database table storing user information

## Requirements

### Requirement 1

**User Story:** As a website visitor, I want to see a chat bubble in the bottom-left corner, so that I can easily access customer support.

#### Acceptance Criteria

1. WHEN the website loads THEN the Chatbot_Widget SHALL display a floating chat bubble icon in the bottom-left corner of the viewport
2. WHEN a user clicks the chat bubble THEN the Chatbot_Widget SHALL expand into a chat interface panel
3. WHEN the chat panel is open and user clicks the close button THEN the Chatbot_Widget SHALL collapse back to the bubble icon
4. WHILE the chat panel is open THEN the Chatbot_Widget SHALL maintain its position fixed to the viewport during scrolling

### Requirement 2

**User Story:** As a user, I want to send messages and receive responses from the AI chatbot, so that I can get help with my inquiries.

#### Acceptance Criteria

1. WHEN a user types a message and presses Enter or clicks send THEN the Chat_API SHALL receive the message and return a response
2. WHEN a message is sent THEN the Chatbot_Widget SHALL display the user message immediately in the chat history
3. WHEN a response is received THEN the Chatbot_Widget SHALL display the bot response in the chat history
4. WHILE waiting for a response THEN the Chatbot_Widget SHALL display a loading indicator
5. IF the Chat_API returns an error THEN the Chatbot_Widget SHALL display an error message to the user

### Requirement 3

**User Story:** As a developer, I want a users table in the database, so that user information can be stored and retrieved for personalization.

#### Acceptance Criteria

1. WHEN the database is initialized THEN the User_Table SHALL be created with columns for id, email, password_hash, name, role, created_at, and last_login
2. WHEN a new user registers THEN the User_System SHALL insert a record into the User_Table with hashed password
3. WHEN a user logs in THEN the User_System SHALL update the last_login timestamp in the User_Table

### Requirement 4

**User Story:** As a user, I want to register and login, so that I can have a personalized chat experience.

#### Acceptance Criteria

1. WHEN a guest user clicks login THEN the Chatbot_Widget SHALL display a login form with email and password fields
2. WHEN a guest user clicks register THEN the Chatbot_Widget SHALL display a registration form with name, email, and password fields
3. WHEN valid credentials are submitted THEN the User_System SHALL authenticate the user and return a session token
4. IF invalid credentials are submitted THEN the User_System SHALL return an error message without revealing which field is incorrect
5. WHEN a user is authenticated THEN the Chatbot_Widget SHALL display the user name and provide a logout option

### Requirement 5

**User Story:** As a system administrator, I want role-based access control, so that different users have appropriate permissions.

#### Acceptance Criteria

1. WHEN a new user registers THEN the Role_Control SHALL assign the default role of customer
2. WHEN a guest user interacts with the chatbot THEN the Role_Control SHALL limit functionality to basic inquiries
3. WHEN a customer user interacts with the chatbot THEN the Role_Control SHALL enable order-specific queries using their user ID
4. WHEN an admin user interacts with the chatbot THEN the Role_Control SHALL enable access to all customer orders and system information

### Requirement 6

**User Story:** As a returning user, I want my chat history preserved, so that I can reference previous conversations.

#### Acceptance Criteria

1. WHEN an authenticated user opens the chat THEN the Chatbot_Widget SHALL load and display their previous chat messages
2. WHEN a new message is sent by an authenticated user THEN the Chat_API SHALL store the message in the database
3. WHEN a user logs out THEN the Chatbot_Widget SHALL clear the displayed chat history from the interface

