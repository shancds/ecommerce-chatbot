-- Seed Data for E-Shop Customer Support Chatbot

-- Clear existing data
TRUNCATE TABLE chat_messages CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE policies CASCADE;
TRUNCATE TABLE rules CASCADE;

-- Insert Users (passwords are bcrypt hashes of 'password123')
-- Hash generated with bcrypt cost factor 12
INSERT INTO users (email, password_hash, name, role, created_at, last_login) VALUES
('customer@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWWQRAOGK2W', 'John Customer', 'customer', '2024-10-01 10:00:00', '2024-11-10 14:30:00'),
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWWQRAOGK2W', 'Admin User', 'admin', '2024-09-15 09:00:00', '2024-11-12 08:00:00'),
('jane@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWWQRAOGK2W', 'Jane Smith', 'customer', '2024-10-20 15:30:00', NULL);

-- Insert Products
INSERT INTO products (id, name, price, category, features, returnable, return_window, stock) VALUES
('P001', 'Wireless Bluetooth Headphones', 79.99, 'Electronics', '["Noise cancellation", "30-hour battery", "Wireless", "Foldable design"]', true, 30, 45),
('P002', 'Smart Fitness Watch', 199.99, 'Electronics', '["Heart rate monitor", "GPS tracking", "Waterproof", "Sleep tracking"]', true, 30, 28),
('P003', 'Running Shoes', 89.99, 'Sports', '["Breathable mesh", "Cushioned sole", "Lightweight", "Durable"]', true, 30, 67),
('P004', 'Yoga Mat', 29.99, 'Sports', '["Non-slip surface", "Extra thick", "Eco-friendly", "Carrying strap"]', true, 30, 120),
('P005', 'Coffee Maker', 149.99, 'Home', '["Programmable", "12-cup capacity", "Auto shut-off", "Reusable filter"]', true, 30, 34),
('P006', 'LED Desk Lamp', 39.99, 'Home', '["Adjustable brightness", "USB charging port", "Touch control", "Energy efficient"]', true, 30, 89),
('P007', 'Laptop Backpack', 59.99, 'Accessories', '["Water resistant", "Padded laptop compartment", "USB charging port", "Anti-theft"]', true, 30, 56),
('P008', 'Wireless Mouse', 24.99, 'Electronics', '["Ergonomic design", "Silent clicks", "Long battery life", "Bluetooth"]', true, 30, 145),
('P009', 'Water Bottle', 19.99, 'Sports', '["Insulated", "BPA-free", "Leak-proof", "24oz capacity"]', true, 30, 203),
('P010', 'Phone Stand', 14.99, 'Accessories', '["Adjustable angle", "Non-slip base", "Foldable", "Universal compatibility"]', true, 30, 178),
('P011', 'Bluetooth Speaker', 69.99, 'Electronics', '["360-degree sound", "Waterproof", "20-hour battery", "Portable"]', true, 30, 42),
('P012', 'Resistance Bands Set', 34.99, 'Sports', '["5 resistance levels", "Portable", "Door anchor included", "Exercise guide"]', true, 30, 91),
('P013', 'Digital Gift Card', 50.00, 'Gift Cards', '["Instant delivery", "No expiration", "Any amount"]', false, 0, 999),
('P014', 'Personalized Mug', 18.99, 'Home', '["Custom text", "Dishwasher safe", "11oz capacity", "Ceramic"]', false, 0, 67),
('P015', 'USB-C Cable', 12.99, 'Electronics', '["Fast charging", "6ft length", "Braided nylon", "Universal"]', true, 30, 234);

-- Insert Orders (with user_id linking to authenticated users)
-- user_id 1 = customer@example.com (John Customer)
-- user_id 3 = jane@example.com (Jane Smith)
INSERT INTO orders (id, product_id, customer_id, user_id, status, order_date, delivery_date, tracking_number, quantity, total) VALUES
('ORD12345', 'P001', 'C001', 1, 'Shipped', '2024-11-01', '2024-11-15', 'TRK789456123', 1, 79.99),
('ORD12346', 'P002', 'C002', 3, 'Processing', '2024-11-10', '2024-11-20', 'TRK789456124', 1, 199.99),
('ORD12347', 'P003', 'C001', 1, 'Delivered', '2024-10-25', '2024-11-05', 'TRK789456125', 2, 179.98),
('ORD12348', 'P005', 'C003', 3, 'Shipped', '2024-11-08', '2024-11-18', 'TRK789456126', 1, 149.99),
('ORD12349', 'P007', 'C004', 1, 'Processing', '2024-11-12', '2024-11-22', 'TRK789456127', 1, 59.99),
('ORD12350', 'P011', 'C002', 3, 'Delivered', '2024-10-20', '2024-10-30', 'TRK789456128', 1, 69.99),
('ORD12351', 'P008', 'C005', 1, 'Shipped', '2024-11-09', '2024-11-19', 'TRK789456129', 3, 74.97),
('ORD12352', 'P004', 'C003', 3, 'Cancelled', '2024-11-05', NULL, NULL, 1, 29.99),
('ORD12353', 'P012', 'C006', 1, 'Processing', '2024-11-11', '2024-11-21', 'TRK789456130', 2, 69.98),
('ORD12354', 'P006', 'C001', 1, 'Delivered', '2024-10-28', '2024-11-07', 'TRK789456131', 1, 39.99);


-- Insert Policies
INSERT INTO policies (policy_type, policy_data) VALUES
('return_policy', '{
  "general": "Items can be returned within 30 days of delivery for a full refund",
  "conditions": [
    "Item must be unused and in original packaging",
    "Receipt or proof of purchase required",
    "Refund processed within 5-7 business days after we receive the item",
    "Original shipping costs are non-refundable",
    "Customer is responsible for return shipping costs"
  ],
  "non_returnable_categories": [
    "Gift Cards",
    "Personalized items",
    "Software downloads",
    "Opened hygiene products"
  ],
  "process": [
    "Contact customer support to initiate return",
    "Receive return authorization number",
    "Pack item securely in original packaging",
    "Ship to our returns center",
    "Refund issued after inspection"
  ]
}'),
('shipping_policy', '{
  "standard": {
    "duration": "5-7 business days",
    "cost": "Free for orders over $50, otherwise $5.99"
  },
  "express": {
    "duration": "2-3 business days",
    "cost": "$14.99"
  },
  "overnight": {
    "duration": "1 business day",
    "cost": "$24.99"
  }
}'),
('warranty_policy', '{
  "electronics": "1 year manufacturer warranty",
  "sports_equipment": "90 days warranty",
  "home_goods": "6 months warranty",
  "accessories": "30 days warranty"
}'),
('faq', '{
  "payment_methods": "We accept Visa, Mastercard, American Express, PayPal, and Apple Pay",
  "order_tracking": "You will receive a tracking number via email once your order ships",
  "international_shipping": "Currently we only ship within the United States",
  "gift_wrapping": "Gift wrapping is available for $4.99 per item",
  "price_match": "We offer price matching within 7 days of purchase"
}');

-- Insert Rules
INSERT INTO rules (id, name, condition, action, priority, response_template) VALUES
('R001', 'Order Status with Order ID', '{"intent": "order_status", "has_order_id": true}', 'get_order_status', 10, 'Your order {order_id} is currently {status}. Expected delivery: {delivery_date}'),
('R002', 'Order Status without Order ID', '{"intent": "order_status", "has_order_id": false}', 'request_order_id', 5, 'I''d be happy to check your order status. Please provide your order number (format: ORD12345).'),
('R003', 'General Return Policy', '{"intent": "return_policy", "has_product_id": false}', 'get_return_policy', 7, 'Our return policy allows returns within 30 days of delivery.'),
('R004', 'Product Specific Return', '{"intent": "return_policy", "has_product_id": true}', 'check_product_returnability', 9, 'Let me check the return policy for that specific product.'),
('R005', 'Product Recommendation', '{"intent": "product_recommendation"}', 'recommend_products', 8, 'Based on your needs, I recommend the following products.'),
('R006', 'Product Information', '{"intent": "product_info", "has_product_id": true}', 'get_product_info', 9, 'Here''s the information about that product.'),
('R007', 'Shipping Policy', '{"intent": "shipping_info"}', 'get_shipping_policy', 7, 'Here''s our shipping information.'),
('R008', 'General Inquiry', '{"intent": "general_inquiry"}', 'provide_general_help', 3, 'I''m here to help! I can assist with order status, returns, product recommendations, and general inquiries.'),
('R009', 'Greeting', '{"intent": "greeting"}', 'greet_user', 6, 'Hello! Welcome to E-Shop customer support. How can I assist you today?'),
('R010', 'Warranty Information', '{"intent": "warranty_info"}', 'get_warranty_info', 7, 'Let me provide you with warranty information.'),
('R011', 'Payment Methods', '{"intent": "payment_info"}', 'get_payment_info', 6, 'Here''s information about our payment methods.'),
('R012', 'Cancellation Request', '{"intent": "cancel_order"}', 'handle_cancellation', 9, 'I can help you with order cancellation.'),
('R013', 'Product Search', '{"intent": "product_search"}', 'search_products_advanced', 8, 'Here are the products matching your search.'),
('R014', 'Order History', '{"intent": "order_history"}', 'get_order_history', 8, 'Here is your order history.'),
('R015', 'User Profile', '{"intent": "user_profile"}', 'get_user_profile', 8, 'Here is your profile information.');
