

-- Clear existing interactions (for clean seed)
TRUNCATE TABLE user_product_interactions CASCADE;

-- User 1 (John Customer) - Interested in Electronics and Sports
INSERT INTO user_product_interactions (user_id, product_id, interaction_type, created_at) VALUES
(1, 'P001', 'click', '2024-11-01 10:00:00'),
(1, 'P001', 'view', '2024-11-01 10:01:00'),
(1, 'P001', 'click', '2024-11-02 14:30:00'),
(1, 'P002', 'click', '2024-11-03 09:15:00'),
(1, 'P002', 'view', '2024-11-03 09:16:00'),
(1, 'P002', 'like', '2024-11-03 09:20:00'),
(1, 'P003', 'click', '2024-11-04 16:00:00'),
(1, 'P003', 'view', '2024-11-04 16:01:00'),
(1, 'P008', 'click', '2024-11-05 11:00:00'),
(1, 'P008', 'click', '2024-11-06 11:30:00'),
(1, 'P008', 'wishlist', '2024-11-06 11:35:00'),
(1, 'P011', 'click', '2024-11-07 13:00:00'),
(1, 'P011', 'view', '2024-11-07 13:05:00'),
(1, 'P015', 'click', '2024-11-08 10:00:00');

-- User 2 (Admin User) - Interested in Home and Accessories
INSERT INTO user_product_interactions (user_id, product_id, interaction_type, created_at) VALUES
(2, 'P005', 'click', '2024-11-01 08:00:00'),
(2, 'P005', 'view', '2024-11-01 08:05:00'),
(2, 'P005', 'click', '2024-11-02 09:00:00'),
(2, 'P005', 'like', '2024-11-02 09:10:00'),
(2, 'P006', 'click', '2024-11-03 14:00:00'),
(2, 'P006', 'view', '2024-11-03 14:02:00'),
(2, 'P006', 'click', '2024-11-04 15:00:00'),
(2, 'P007', 'click', '2024-11-05 10:00:00'),
(2, 'P007', 'wishlist', '2024-11-05 10:05:00'),
(2, 'P010', 'click', '2024-11-06 11:00:00'),
(2, 'P010', 'view', '2024-11-06 11:02:00'),
(2, 'P014', 'click', '2024-11-07 16:00:00'),
(2, 'P014', 'click', '2024-11-08 09:00:00');

-- User 3 (Jane Smith) - Interested in Sports and Electronics
INSERT INTO user_product_interactions (user_id, product_id, interaction_type, created) VALUES
(3, 'P003', 'click', '2024-11-01 12:00:00'),
(3, 'P003', 'view', '2024-11-01 12:05:00'),
(3, 'P003', 'click', '2024-11-02 13:00:00'),
(3, 'P004', 'click', '2024-11-03 10:00:00'),
(3, 'P004', 'view', '2024-11-03 10:02:00'),
(3, 'P004', 'click', '2024-11-04 11:00:00'),
(3, 'P004', 'wishlist', '2024-11-04 11:05:00'),
(3, 'P009', 'view', '2024-11-05 14:02:00'),
(3, 'P012', 'click', '2024-11-06 09:00:00'),
(3, 'P012', 'click', '2024-11-07 10:00:00'),
(3, 'P002', 'click', '2024-11-08 15:00:00'),
(3, 'P002', 'view', '2024-11-08 15:05:00');

-- User 4 (Mike Johnson) - Interested in Electronics and Accessories
INSERT INTO user_product_interactions (user_id, product_id, interaction_type, created_at) VALUES
(4, 'P001', 'click', '2024-11-01 09:00:00'),
(4, 'P001', 'view', '2024-11-01 09:05:00'),
(4, 'P001', 'click', '2024-11-02 10:00:00'),
(4, 'P001', 'click', '2024-11-03 11:00:00'),
(4, 'P001', 'like', '2024-11-03 11:05:00'),
(4, 'P008', 'view', '2024-11-04 14:02:0'),
(4, 'P008', 'click', '2024-11-05 15:00:00'),
(4, 'P010', 'view', '2024-11-06 10:02:00'),
(4, 'P010', 'click', '2024-11-07 11:00:00'),
(4, 'P010', 'wishlist', '2024-11-07 11:05:00'),
(4, 'P007', 'click', '2024-11-08 13:00:00'),
(4, 'P015', 'click', '2024-11-09 09:00:00');
