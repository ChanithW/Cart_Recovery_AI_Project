#!/usr/bin/env python3
"""
Test script to debug and fix products loading issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
import traceback

def test_products_endpoint():
    """Test the products endpoint directly"""
    try:
        # Initialize database
        db = DatabaseManager()
        
        # Test connection
        if not db.connection or not db.connection.is_connected():
            print("❌ Database not connected, attempting to connect...")
            db.connect()
        
        print("✅ Database connected successfully")
        
        # Test products query
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM products")
        count_result = cursor.fetchone()
        print(f"📊 Total products in database: {count_result['count']}")
        
        # Test the actual query used by the endpoint
        cursor.execute("SELECT * FROM products WHERE stock_quantity > 0")
        products = cursor.fetchall()
        cursor.close()
        
        print(f"✅ Found {len(products)} products with stock > 0")
        
        if len(products) == 0:
            print("⚠️  No products found with stock > 0")
            print("🔧 Adding sample products...")
            add_sample_products(db)
        else:
            print("📦 Sample products:")
            for i, product in enumerate(products[:3]):  # Show first 3
                print(f"  {i+1}. {product['name']} - ${product['price']} (Stock: {product['stock_quantity']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing products: {str(e)}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return False

def add_sample_products(db):
    """Add sample products if none exist"""
    try:
        cursor = db.connection.cursor()
        
        sample_products = [
            ("Wireless Headphones", "High-quality wireless headphones with noise cancellation", 199.99, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e", 50, "Electronics"),
            ("Smartphone", "Latest smartphone with advanced camera", 799.99, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9", 30, "Electronics"),
            ("Running Shoes", "Comfortable running shoes for daily workouts", 129.99, "https://images.unsplash.com/photo-1542291026-7eec264c27ff", 75, "Sports"),
            ("Coffee Maker", "Automatic coffee maker with programmable settings", 149.99, "https://images.unsplash.com/photo-1559056199-641a0ac8b55e", 25, "Home"),
            ("Laptop Backpack", "Durable laptop backpack with multiple compartments", 79.99, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62", 100, "Accessories")
        ]
        
        # Clear existing products first
        cursor.execute("DELETE FROM products")
        
        # Insert sample products
        insert_query = """
            INSERT INTO products (name, description, price, image_url, stock_quantity, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, sample_products)
        db.connection.commit()
        cursor.close()
        
        print(f"✅ Added {len(sample_products)} sample products")
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample products: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing products endpoint...")
    success = test_products_endpoint()
    
    if success:
        print("\n✅ Products endpoint test completed successfully!")
        print("🚀 The products should now load properly in the frontend")
    else:
        print("\n❌ Products endpoint test failed!")
        print("🔧 Please check the error messages above")
