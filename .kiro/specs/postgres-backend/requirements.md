# Requirements Document

## Introduction

This specification defines the requirements for integrating PostgreSQL database backend into the existing E-Shop Customer Support Chatbot. The current system uses JSON files for data storage (products, orders, policies, rules). This feature will migrate the data layer to PostgreSQL while maintaining the existing chatbot functionality, and expose the chatbot as a REST API backend for frontend integration.

## Glossary

- **Chatbot_Backend**: The Python-based REST API server that handles chatbot requests
- **Database_Layer**: The PostgreSQL database connection and query module
- **Knowledge_Base**: The component that retrieves products, orders, policies, and rules data
- **API_Endpoint**: A REST endpoint that accepts user messages and returns chatbot responses

## Requirements

### Requirement 1

**User Story:** As a developer, I want to connect the chatbot to a PostgreSQL database, so that data is stored persistently and can be managed externally.

#### Acceptance Criteria

1. WHEN the Chatbot_Backend starts THEN the Database_Layer SHALL establish a connection to the PostgreSQL database using environment variables for configuration
2. WHEN the database connection fails THEN the Database_Layer SHALL log the error and raise an appropriate exception
3. WHEN the Chatbot_Backend shuts down THEN the Database_Layer SHALL close all database connections gracefully

### Requirement 2

**User Story:** As a developer, I want database tables created for products, orders, policies, and rules, so that the existing JSON data structure is preserved in PostgreSQL.

#### Acceptance Criteria

1. WHEN the database is initialized THEN the Database_Layer SHALL create a products table with columns for id, name, price, category, features, returnable, return_window, and stock
2. WHEN the database is initialized THEN the Database_Layer SHALL create an orders table with columns for id, product_id, customer_id, status, order_date, delivery_date, tracking_number, quantity, and total
3. WHEN the database is initialized THEN the Database_Layer SHALL create a policies table with columns for id, policy_type, and policy_data as JSON
4. WHEN the database is initialized THEN the Database_Layer SHALL create a rules table with columns for id, name, condition, action, priority, and response_template

### Requirement 3

**User Story:** As a developer, I want the Knowledge Base to query PostgreSQL instead of JSON files, so that the chatbot uses database-stored data.

#### Acceptance Criteria

1. WHEN the Knowledge_Base retrieves a product THEN the Database_Layer SHALL query the products table and return the product data
2. WHEN the Knowledge_Base retrieves an order THEN the Database_Layer SHALL query the orders table and return the order data
3. WHEN the Knowledge_Base retrieves policies THEN the Database_Layer SHALL query the policies table and return the policy data
4. WHEN the Knowledge_Base retrieves rules THEN the Database_Layer SHALL query the rules table and return all rules
5. WHEN the Knowledge_Base searches products by category or price THEN the Database_Layer SHALL execute a filtered query and return matching products

### Requirement 4

**User Story:** As a frontend developer, I want a REST API endpoint to send messages and receive chatbot responses, so that I can build a web frontend for the chatbot.

#### Acceptance Criteria

1. WHEN a POST request is sent to /api/chat with a message THEN the API_Endpoint SHALL process the message through the chatbot agent and return the response as JSON
2. WHEN the /api/chat endpoint receives an empty message THEN the API_Endpoint SHALL return a 400 error with an appropriate message
3. WHEN a GET request is sent to /api/health THEN the API_Endpoint SHALL return the server and database connection status

### Requirement 5

**User Story:** As a developer, I want SQL scripts to create tables and insert sample data, so that I can manually set up the database.

#### Acceptance Criteria

1. WHEN the developer needs to set up the database THEN the system SHALL provide a SQL script that creates all required tables
2. WHEN the developer needs sample data THEN the system SHALL provide a SQL script that inserts the existing JSON data into the database tables
