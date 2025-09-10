#!/usr/bin/env python3
"""Test email generation with new API key"""

from ai_agent import AIAgent
from config import Config

def test_email_generation():
    print("Testing email generation with new API key...")
    print(f"Using API key: {Config.OPENROUTER_API_KEY[:20]}...")
    
    try:
        # Initialize AI agent
        agent = AIAgent(api_key=Config.OPENROUTER_API_KEY)
        
        # Test email generation
        result = agent.generate_recovery_email(
            user_name="Test Customer",
            cart_items="Laptop, Wireless Mouse",
            cart_value=150.0
        )
        
        print("✅ Email generation successful!")
        print(f"Subject: {result['subject']}")
        print(f"Body preview: {result['body'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Email generation failed: {e}")
        return False

if __name__ == "__main__":
    test_email_generation()
