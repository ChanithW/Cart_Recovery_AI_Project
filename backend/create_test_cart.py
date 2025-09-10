#!/usr/bin/env python3
"""Create a test abandoned cart"""

import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def create_test_cart():
    print("Creating a test cart that will become abandoned...")
    
    # Create a unique session ID
    session_id = str(uuid.uuid4())
    
    # Test 1: Add items to cart using the correct endpoint
    print(f"📦 Adding items to cart (session: {session_id[:8]}...)")
    
    cart_update = {
        "session_id": session_id,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cart/update", json=cart_update)
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Cart created successfully!")
        else:
            print(f"   ❌ Cart creation failed: {response.text}")
            return False
            
        # Test 2: Check if cart exists
        print(f"\n🔍 Checking cart contents...")
        cart_response = requests.get(f"{BASE_URL}/cart/{session_id}")
        
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            print(f"   Cart total: ${cart_data.get('total', 0):.2f}")
            print(f"   Items count: {len(cart_data.get('items', []))}")
        
        # Test 3: Check analytics
        print(f"\n📊 Checking current analytics...")
        analytics_response = requests.get(f"{BASE_URL}/analytics/abandoned-carts")
        
        if analytics_response.status_code == 200:
            data = analytics_response.json()
            print(f"   Total carts: {data.get('total_abandoned', 0)}")
            print(f"   Total value: ${data.get('total_value', 0):.2f}")
            
            if data.get('carts'):
                print("   Cart details:")
                for cart in data['carts']:
                    print(f"     - ID: {cart.get('id')} | Value: ${cart.get('total_value', 0):.2f} | Updated: {cart.get('updated_at')}")
        
        print(f"\n💡 To test abandonment:")
        print(f"   1. Wait 30+ minutes")
        print(f"   2. Check http://localhost:8000/admin")
        print(f"   3. The cart should appear as abandoned")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_test_cart()
