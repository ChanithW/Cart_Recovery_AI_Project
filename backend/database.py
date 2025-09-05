import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, host="localhost", user="root", password="", database="cart_recovery_ai"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def create_database_and_tables(self):
        """Create database and all required tables"""
        try:
            # Create database if not exists
            temp_conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = temp_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            temp_conn.close()
            
            # Connect to the database
            self.connect()
            cursor = self.connection.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL,
                    image_url VARCHAR(500),
                    stock_quantity INT DEFAULT 0,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Shopping carts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_carts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    session_id VARCHAR(255),
                    status ENUM('active', 'abandoned', 'recovered', 'completed') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    abandoned_at TIMESTAMP NULL,
                    total_value DECIMAL(10, 2) DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Cart items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cart_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    price DECIMAL(10, 2) NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            
            # Recovery attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_attempts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cart_id INT NOT NULL,
                    email_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email_subject VARCHAR(255),
                    email_content TEXT,
                    offer_type VARCHAR(100),
                    offer_value DECIMAL(10, 2),
                    opened BOOLEAN DEFAULT FALSE,
                    clicked BOOLEAN DEFAULT FALSE,
                    recovered BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (cart_id) REFERENCES shopping_carts(id) ON DELETE CASCADE
                )
            """)
            
            # Insert sample products
            sample_products = [
                ("Wireless Headphones", "High-quality wireless headphones with noise cancellation", 199.99, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e", 50, "Electronics"),
                ("Smartphone", "Latest smartphone with advanced camera", 799.99, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9", 30, "Electronics"),
                ("Running Shoes", "Comfortable running shoes for daily workouts", 129.99, "https://images.unsplash.com/photo-1542291026-7eec264c27ff", 75, "Sports"),
                ("Coffee Maker", "Automatic coffee maker with programmable settings", 149.99, "https://images.unsplash.com/photo-1559056199-641a0ac8b55e", 25, "Home"),
                ("Laptop Backpack", "Durable laptop backpack with multiple compartments", 79.99, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62", 100, "Accessories"),
                ("Gaming Mouse", "Precision gaming mouse with RGB lighting", 89.99, "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46", 60, "Electronics"),
                ("Yoga Mat", "Non-slip yoga mat for home workouts", 39.99, "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b", 200, "Sports"),
                ("Bluetooth Speaker", "Portable Bluetooth speaker with deep bass", 69.99, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1", 80, "Electronics")
            ]
            
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                insert_query = """
                    INSERT INTO products (name, description, price, image_url, stock_quantity, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.executemany(insert_query, sample_products)
            
            cursor.close()
            print("Database and tables created successfully!")
            return True
            
        except Error as e:
            print(f"Error creating database/tables: {e}")
            return False
    
    def get_abandoned_carts(self, minutes_threshold=30):
        """Get carts that have been abandoned for more than threshold minutes"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT sc.*, u.email, 
                       CONCAT(u.first_name, ' ', u.last_name) as name,
                       GROUP_CONCAT(CONCAT(p.name, ' (', ci.quantity, ')') SEPARATOR ', ') as items
                FROM shopping_carts sc
                LEFT JOIN users u ON sc.user_id = u.id
                LEFT JOIN cart_items ci ON sc.id = ci.cart_id
                LEFT JOIN products p ON ci.product_id = p.id
                WHERE sc.status = 'active' 
                AND sc.updated_at < NOW() - INTERVAL %s MINUTE
                AND sc.total_value > 0
                GROUP BY sc.id
            """
            cursor.execute(query, (minutes_threshold,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting abandoned carts: {e}")
            return []
    
    def mark_cart_abandoned(self, cart_id):
        """Mark a cart as abandoned"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE shopping_carts 
                SET status = 'abandoned', abandoned_at = NOW()
                WHERE id = %s
            """, (cart_id,))
            return True
        except Error as e:
            print(f"Error marking cart as abandoned: {e}")
            return False
    
    def create_user(self, email, first_name, last_name, password_hash):
        """Create a new user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO users (email, first_name, last_name, password_hash)
                VALUES (%s, %s, %s, %s)
            """, (email, first_name, last_name, password_hash))
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def close(self):
        if self.connection:
            self.connection.close()

# Initialize database
db = DatabaseManager()
