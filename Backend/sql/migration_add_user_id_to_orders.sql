-- Migration: Add user_id column to orders table
-- This migration links orders to authenticated users via the users table
-- Requirements: 2.1, 2.3

-- Add user_id column with foreign key reference to users(id)
ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id);

-- Create index for query performance
CREATE INDEX idx_orders_user_id ON orders(user_id);
