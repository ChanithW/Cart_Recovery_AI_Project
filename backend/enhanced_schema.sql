-- Additional tables for GDPR compliance and enhanced features

-- Email preferences for unsubscribe functionality
CREATE TABLE IF NOT EXISTS email_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    unsubscribed BOOLEAN DEFAULT FALSE,
    unsubscribe_date DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_unsubscribed (unsubscribed)
);

-- User privacy settings
CREATE TABLE IF NOT EXISTS user_privacy_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_marketing BOOLEAN DEFAULT TRUE,
    data_analytics BOOLEAN DEFAULT TRUE,
    personalization BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_privacy (user_id)
);

-- Chat sessions for tracking assistant conversations
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME NULL,
    message_count INT DEFAULT 0,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_last_activity (last_activity)
);

-- Chat messages for conversation history
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    sender_type ENUM('user', 'assistant') NOT NULL,
    message_text TEXT NOT NULL,
    message_data JSON NULL, -- Store structured data like recommendations
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- AI performance analytics
CREATE TABLE IF NOT EXISTS ai_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL, -- 'email_sent', 'offer_generated', 'chat_session', etc.
    user_id INT NULL,
    cart_id INT NULL,
    ai_model VARCHAR(100) NOT NULL,
    input_data JSON NULL,
    output_data JSON NULL,
    response_time_ms INT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE SET NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success)
);

-- Product recommendations tracking
CREATE TABLE IF NOT EXISTS recommendation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    session_id VARCHAR(255) NULL,
    recommended_product_ids JSON NOT NULL, -- Array of product IDs
    recommendation_reason VARCHAR(255) NULL,
    cart_context JSON NULL, -- Cart state when recommendation was made
    clicked_products JSON NULL, -- Which recommendations were clicked
    conversion_products JSON NULL, -- Which recommendations led to purchase
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- Enhanced user behavior tracking
CREATE TABLE IF NOT EXISTS user_behavior_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    session_id VARCHAR(255) NULL,
    event_type VARCHAR(100) NOT NULL, -- 'page_view', 'product_view', 'cart_add', 'cart_remove', 'search', etc.
    event_data JSON NULL, -- Product ID, search terms, etc.
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp)
);

-- Product categories for better recommendations
CREATE TABLE IF NOT EXISTS product_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_category_id INT NULL,
    description TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES product_categories(id) ON DELETE SET NULL,
    INDEX idx_parent_category (parent_category_id)
);

-- Link products to categories (many-to-many)
CREATE TABLE IF NOT EXISTS product_category_links (
    product_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES product_categories(id) ON DELETE CASCADE
);

-- Insert some default categories
INSERT IGNORE INTO product_categories (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Home & Garden', 'Home improvement and garden supplies'),
('Sports & Outdoors', 'Sports equipment and outdoor gear'),
('Books & Media', 'Books, movies, music, and digital media'),
('Health & Beauty', 'Health, wellness, and beauty products'),
('Toys & Games', 'Toys, games, and hobby items'),
('Food & Beverages', 'Food, drinks, and grocery items');
