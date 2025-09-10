#!/usr/bin/env python3
"""
Script to create a test user and an abandoned cart with customer information
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_test_user():
    """Create a test user"""
    user_data = {
        "email": "john.doe@example.com",
        "password": "testpass123",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    print("Creating test user...")
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ User created successfully: {result['user']['email']}")
        return result['access_token'], result['user']['id']
    else:
        print(f"❌ Failed to create user: {response.status_code} - {response.text}")
        # Try to login if user already exists
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
        if login_response.status_code == 200:
            token_data = login_response.json()
            print("✅ User already exists, logged in successfully")
            # Get user ID
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            if profile_response.status_code == 200:
                user_info = profile_response.json()
                return token_data['access_token'], user_info['id']
        return None, None

def create_cart_with_user(access_token, user_id):
    """Create a cart for the user and add items"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("Creating cart for user...")
    
    # Create cart with items using the update endpoint
    cart_data = {
        "user_id": user_id,
        "session_id": None,
        "items": [
            {"product_id": 1, "quantity": 1},  # Smartphone
            {"product_id": 3, "quantity": 2},  # Wireless Headphones
        ]
    }
    
    response = requests.post(f"{BASE_URL}/cart/update", json=cart_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cart created with ID: {result['cart_id']}, Total: ${result['total_value']}")
        return result['cart_id']
    else:
        print(f"❌ Failed to create cart: {response.status_code} - {response.text}")
        return None

def main():
    print("=== Creating Test User with Abandoned Cart ===")
    
    # Create test user
    access_token, user_id = create_test_user()
    if not access_token:
        print("❌ Failed to create/login user")
        return
    
    # Create cart with items
    cart_id = create_cart_with_user(access_token, user_id)
    if not cart_id:
        print("❌ Failed to create cart")
        return
    
    print(f"\n✅ Successfully created cart {cart_id} for user {user_id}")
    print("💡 This cart will be marked as abandoned by the monitoring service within 1 minute")
    print("🔄 Check the admin dashboard to see the cart with customer information!")

if __name__ == "__main__":
    main()
