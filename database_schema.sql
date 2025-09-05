-- Cart Recovery AI Database Schema
-- MySQL Database Schema for E-commerce Cart Recovery System

-- Create the database
CREATE DATABASE IF NOT EXISTS cart_recovery_ai;
USE cart_recovery_ai;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500),
    stock_quantity INT DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Shopping carts table
CREATE TABLE IF NOT EXISTS shopping_carts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    session_id VARCHAR(255) NOT NULL,
    status ENUM('active', 'abandoned', 'recovered', 'completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    abandoned_at TIMESTAMP NULL,
    recovered_at TIMESTAMP NULL,
    total_value DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_status (session_id, status),
    INDEX idx_status_updated (status, updated_at)
);

-- Cart items table
CREATE TABLE IF NOT EXISTS cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cart_product (cart_id, product_id)
);

-- Recovery attempts table
CREATE TABLE IF NOT EXISTS recovery_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT NOT NULL,
    email_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_subject VARCHAR(255),
    email_content TEXT,
    offer_type VARCHAR(100),
    offer_value DECIMAL(10, 2) DEFAULT 0,
    opened BOOLEAN DEFAULT FALSE,
    clicked BOOLEAN DEFAULT FALSE,
    recovered BOOLEAN DEFAULT FALSE,
    recovery_method VARCHAR(50), -- 'email', 'popup', 'sms', etc.
    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id) ON DELETE CASCADE,
    INDEX idx_cart_sent (cart_id, email_sent_at)
);

-- Orders table (for completed purchases)
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT,
    user_id INT,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    payment_method VARCHAR(50),
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User behavior tracking table
CREATE TABLE IF NOT EXISTS user_behavior (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    session_id VARCHAR(255),
    action VARCHAR(100), -- 'page_view', 'add_to_cart', 'remove_from_cart', 'checkout_start', etc.
    page_url VARCHAR(500),
    product_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON, -- Additional data like time spent, scroll depth, etc.
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_user_action (user_id, action),
    INDEX idx_session_timestamp (session_id, timestamp)
);

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject_template TEXT,
    body_template TEXT,
    template_type ENUM('recovery', 'welcome', 'promotional') DEFAULT 'recovery',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- A/B test results table
CREATE TABLE IF NOT EXISTS ab_test_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_name VARCHAR(255),
    variant VARCHAR(100),
    cart_id INT,
    recovery_attempt_id INT,
    converted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id),
    FOREIGN KEY (recovery_attempt_id) REFERENCES recovery_attempts(id),
    INDEX idx_test_variant (test_name, variant)
);

-- Insert sample products
INSERT INTO products (name, description, price, image_url, stock_quantity, category) VALUES
('Wireless Headphones', 'High-quality wireless headphones with noise cancellation', 199.99, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e', 50, 'Electronics'),
('Smartphone', 'Latest smartphone with advanced camera and features', 799.99, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9', 30, 'Electronics'),
('Running Shoes', 'Comfortable running shoes for daily workouts', 129.99, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff', 75, 'Sports'),
('Coffee Maker', 'Automatic coffee maker with programmable settings', 149.99, 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e', 25, 'Home'),
('Laptop Backpack', 'Durable laptop backpack with multiple compartments', 79.99, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62', 100, 'Accessories'),
('Gaming Mouse', 'Precision gaming mouse with RGB lighting', 89.99, 'https://images.unsplash.com/photo-1527864550417-7fd91fc009e0b', 60, 'Electronics'),
('Yoga Mat', 'Non-slip yoga mat for home workouts', 39.99, 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b', 200, 'Sports'),
('Bluetooth Speaker', 'Portable Bluetooth speaker with deep bass', 69.99, 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1', 80, 'Electronics'),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 45.99, 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c', 120, 'Home'),
('Water Bottle', 'Insulated stainless steel water bottle', 24.99, 'https://images.unsplash.com/photo-1602143407151-7111542de6e8', 150, 'Sports');

-- Insert sample email templates
INSERT INTO email_templates (name, subject_template, body_template, template_type) VALUES
('Default Recovery', 'You left something behind, {customer_name}!', 
'Hi {customer_name},

We noticed you left some great items in your cart:
{cart_items}

Don''t miss out on these amazing products worth ${cart_value}!

{offer_text}

Complete your purchase now: {checkout_link}

Best regards,
The Team', 'recovery'),

('Urgent Recovery', 'Only a few left! Complete your order, {customer_name}', 
'Hi {customer_name},

Your cart is about to expire! You have:
{cart_items}

Stock is running low on these items. Secure yours now with {offer_text}

{checkout_link}

Hurry, this offer expires soon!

Best,
The Team', 'recovery');

-- Create views for analytics
CREATE VIEW abandoned_cart_analytics AS
SELECT 
    DATE(abandoned_at) as abandon_date,
    COUNT(*) as abandoned_count,
    SUM(total_value) as lost_revenue,
    AVG(total_value) as avg_cart_value
FROM shopping_carts 
WHERE status = 'abandoned' 
AND abandoned_at IS NOT NULL
GROUP BY DATE(abandoned_at);

CREATE VIEW recovery_performance AS
SELECT 
    r.offer_type,
    COUNT(*) as attempts,
    SUM(r.recovered) as recoveries,
    (SUM(r.recovered) / COUNT(*)) * 100 as recovery_rate,
    AVG(sc.total_value) as avg_recovered_value
FROM recovery_attempts r
JOIN shopping_carts sc ON r.cart_id = sc.id
GROUP BY r.offer_type;
