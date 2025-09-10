#!/usr/bin/env python3
"""Test script to validate OpenRouter API key"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openrouter_api():
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")
    
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found in environment")
        return False
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        # Test with a simple request
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[{"role": "user", "content": "Hello, this is a test"}],
            max_tokens=10
        )
        
        print("✅ API key is valid!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing OpenRouter API key...")
    test_openrouter_api()
