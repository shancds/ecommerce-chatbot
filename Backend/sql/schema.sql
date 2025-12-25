-- PostgreSQL Schema for E-Shop Customer Support Chatbot

DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS rules CASCADE;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'customer',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Chat messages table
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_bot BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    features JSON NOT NULL,
    returnable BOOLEAN NOT NULL DEFAULT true,
    return_window INTEGER NOT NULL DEFAULT 30,
    stock INTEGER NOT NULL DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    id VARCHAR(10) PRIMARY KEY,
    product_id VARCHAR(10) NOT NULL REFERENCES products(id),
    customer_id VARCHAR(10) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE,
    tracking_number VARCHAR(50),
    quantity INTEGER NOT NULL DEFAULT 1,
    total DECIMAL(10,2) NOT NULL
);

-- Policies table
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,
    policy_type VARCHAR(50) UNIQUE NOT NULL,
    policy_data JSON NOT NULL
);

-- Rules table
CREATE TABLE rules (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    condition JSON NOT NULL,
    action VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    response_template TEXT NOT NULL
);

-- Create indexes for common queries
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_rules_priority ON rules(priority DESC);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);
