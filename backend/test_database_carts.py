#!/usr/bin/env python3
"""Direct database check for abandoned carts"""

from database import DatabaseManager
from datetime import datetime, timedelta

def check_database_directly():
    print("🔍 Checking database directly for abandoned carts...")
    
    try:
        db = DatabaseManager()
        
        # Get all carts from database
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM carts ORDER BY updated_at DESC LIMIT 10")
        carts = cursor.fetchall()
        
        print(f"\n📊 Total carts in database: {len(carts)}")
        
        if carts:
            print("\nRecent carts:")
            for cart in carts:
                age_minutes = (datetime.now() - cart['updated_at']).total_seconds() / 60
                status = "🔴 ABANDONED" if age_minutes > 30 else "🟢 ACTIVE"
                print(f"   Cart {cart['id']}: ${cart['total_value']:.2f} - {status} ({age_minutes:.1f} min old)")
        
        # Check specifically for abandoned carts using the same logic as the API
        abandoned_carts = db.get_abandoned_carts(minutes_threshold=30)
        print(f"\n🚨 Abandoned carts (>30 min): {len(abandoned_carts)}")
        
        for cart in abandoned_carts:
            print(f"   - Cart {cart['id']}: ${cart['total_value']:.2f}")
            print(f"     Items: {cart.get('items', 'No items')}")
            print(f"     Last updated: {cart['updated_at']}")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    check_database_directly()
