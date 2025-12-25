# Implementation Plan

- [x] 1. Set up database schema for users and chat history





  - [x] 1.1 Add users table to sql/schema.sql


    - Create users table with id, email, password_hash, name, role, created_at, last_login
    - Add unique constraint on email
    - _Requirements: 3.1_

  - [x] 1.2 Add chat_messages table to sql/schema.sql

    - Create chat_messages table with id, user_id, message, is_bot, created_at
    - Add foreign key to users table

    - _Requirements: 6.2_
  - [x] 1.3 Add sample users to sql/seed_data.sql

    - Insert test users with different roles (customer, admin)
    - _Requirements: 3.1_

- [x] 2. Implement backend authentication system





  - [x] 2.1 Add authentication dependencies to requirements.txt


    - Add PyJWT, bcrypt packages
    - _Requirements: 4.3_

  - [x] 2.2 Add user database methods to src/database.py

    - Implement create_user(), get_user_by_email(), update_last_login()
    - Implement save_chat_message(), get_chat_history()
    - _Requirements: 3.2, 3.3, 6.2_
  - [ ]* 2.3 Write property test for password hashing
    - **Property 3: Password hashing**
    - **Validates: Requirements 3.2**
  - [ ]* 2.4 Write property test for login timestamp update
    - **Property 4: Login timestamp update**
    - **Validates: Requirements 3.3**

  - [x] 2.5 Implement auth endpoints in src/api.py

    - Add /api/auth/register, /api/auth/login, /api/auth/logout, /api/auth/me
    - Implement JWT token generation and validation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 2.6 Write property test for authentication token validity
    - **Property 5: Authentication token validity**
    - **Validates: Requirements 4.3**
  - [ ]* 2.7 Write property test for generic error messages
    - **Property 6: Generic error messages**
    - **Validates: Requirements 4.4**
  - [ ]* 2.8 Write property test for default role assignment
    - **Property 7: Default role assignment**
    - **Validates: Requirements 5.1**

- [x] 3. Implement chat history endpoints





  - [x] 3.1 Add chat history endpoint to src/api.py


    - Implement GET /api/history for authenticated users
    - _Requirements: 6.1_

  - [x] 3.2 Modify /api/chat to store messages for authenticated users

    - Save user message and bot response to database
    - Include user context in chat processing
    - _Requirements: 6.2, 5.3, 5.4_
  - [ ]* 3.3 Write property test for chat history persistence
    - **Property 8: Chat history persistence**
    - **Validates: Requirements 6.1, 6.2**

- [ ] 4. Checkpoint - Ensure all backend tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Set up React frontend project






  - [x] 5.1 Create frontend directory with Vite React project

    - Initialize Vite with React template
    - Configure proxy for API calls to backend
    - _Requirements: 1.1_

  - [x] 5.2 Create base CSS styles

    - Add global styles and CSS variables
    - Create component-specific CSS modules
    - _Requirements: 1.1, 1.4_

- [-] 6. Implement ChatWidget components



  - [x] 6.1 Create ChatBubble component


    - Floating button with chat icon in bottom-left
    - Notification badge for unread messages
    - _Requirements: 1.1, 1.2_
  - [x] 6.2 Create ChatPanel component


    - Header with user info or auth buttons
    - Message list with user/bot styling
    - Input area with send button
    - _Requirements: 1.2, 1.3, 2.2, 2.3, 2.4_
  - [x] 6.3 Create ChatWidget container component


    - Manage open/closed state
    - Handle message sending and receiving
    - Integrate with auth context
    - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.5_
  - [ ]* 6.4 Write property test for chat API response format
    - **Property 1: Chat API response format**
    - **Validates: Requirements 2.1**
  - [ ]* 6.5 Write property test for user message display
    - **Property 2: User message display**
    - **Validates: Requirements 2.2, 2.3**

- [x] 7. Implement authentication UI










  - [x] 7.1 Create AuthForm component


    - Login form with email/password fields
    - Register form with name/email/password fields
    - Form validation and error display
    - _Requirements: 4.1, 4.2, 4.4_
  - [x] 7.2 Create AuthContext for state management


    - Store user info and token
    - Provide login/logout/register functions
    - Persist token in localStorage
    - _Requirements: 4.3, 4.5, 6.3_
  - [x] 7.3 Integrate auth with ChatWidget


    - Show auth buttons for guests
    - Show user name and logout for authenticated
    - Load chat history on login
    - _Requirements: 4.5, 5.2, 5.3, 6.1, 6.3_

- [-] 8. Create API service layer




  - [x] 8.1 Create api service module

    - Implement chat, auth, and history API calls
    - Handle token attachment and refresh
    - _Requirements: 2.1, 4.3, 6.1_

- [x] 9. Create demo page






  - [x] 9.1 Create simple demo website page

    - Basic page layout to demonstrate widget
    - Include ChatWidget component
    - _Requirements: 1.1_

- [x] 10. Final Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
