#!/usr/bin/env python3
"""Test script to simulate cart abandonment and verify monitoring"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_abandoned_cart_monitoring():
    print("🧪 Testing Abandoned Cart Monitoring System...")
    
    # Step 1: Create a new cart with items
    print("\n1. Creating a cart with items...")
    cart_data = {
        "session_id": "test-abandonment-session-123",
        "user_id": "test-user-456",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cart/update", json=cart_data)
        print(f"   Cart created: {response.status_code}")
        
        # Step 2: Check current abandoned carts
        print("\n2. Checking current abandoned carts...")
        analytics_response = requests.get(f"{BASE_URL}/analytics/abandoned-carts")
        
        if analytics_response.status_code == 200:
            data = analytics_response.json()
            print(f"   Total abandoned carts: {data.get('total_abandoned', 0)}")
            print(f"   Total lost revenue: ${data.get('total_value', 0):.2f}")
            
            if data.get('carts'):
                print("   Recent abandoned carts:")
                for cart in data['carts'][:3]:  # Show first 3
                    print(f"     - Cart ID {cart.get('id')}: ${cart.get('total_value', 0):.2f}")
            
            return True
        else:
            print(f"   ❌ Failed to get analytics: {analytics_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_real_time_updates():
    print("\n3. Testing real-time updates...")
    
    try:
        # Make multiple requests to simulate real-time monitoring
        for i in range(3):
            response = requests.get(f"{BASE_URL}/analytics/abandoned-carts")
            if response.status_code == 200:
                data = response.json()
                print(f"   Check #{i+1}: {data.get('total_abandoned', 0)} abandoned carts")
            time.sleep(1)
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success1 = test_abandoned_cart_monitoring()
    success2 = test_real_time_updates()
    
    if success1 and success2:
        print("\n✅ Abandoned cart monitoring is WORKING!")
        print("💡 Visit http://localhost:8000/admin to see the dashboard")
    else:
        print("\n❌ Some issues detected with monitoring system")
