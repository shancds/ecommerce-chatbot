-- Migration: Add user_product_interactions table
-- Description: Track user interactions with products for personalized recommendations

-- Create user_product_interactions table
CREATE TABLE IF NOT EXISTS user_product_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id VARCHAR(10) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('click', 'like', 'share', 'view', 'wishlist')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON user_product_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_product_id ON user_product_interactions(product_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON user_product_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON user_product_interactions(created_at DESC);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_interactions_user_product ON user_product_interactions(user_id, product_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type_count ON user_product_interactions(product_id, interaction_type);
