#!/usr/bin/env python3
"""
Simple API test to verify endpoints are working
"""
import requests
import json

def test_api_endpoints():
    """Test all major API endpoints"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/health",
        "/products", 
        "/analytics/abandoned-carts"
    ]
    
    print("🔍 Testing API endpoints...")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n📡 Testing: {url}")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK (Status: {response.status_code})")
                
                # For products endpoint, show count
                if endpoint == "/products":
                    data = response.json()
                    print(f"   📦 Found {len(data)} products")
                    
            else:
                print(f"❌ {endpoint}: Failed (Status: {response.status_code})")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused - server not running?")
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint}: Request timeout")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {str(e)}")
    
    print("\n🔍 Testing CORS headers...")
    try:
        response = requests.options(f"{base_url}/products")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        if cors_headers:
            print("✅ CORS headers found:")
            for header, value in cors_headers.items():
                print(f"   {header}: {value}")
        else:
            print("⚠️  No CORS headers found")
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()
