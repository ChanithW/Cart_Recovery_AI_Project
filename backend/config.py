# Cart Recovery AI - Configuration
import os
from typing import Dict, Any

class Config:
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "cart_recovery_ai")
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL = "deepseek/deepseek-chat-v3.1:free"
    
    # Site Configuration
    SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")
    SITE_NAME = os.getenv("SITE_NAME", "Cart Recovery AI")
    
    # Cart Abandonment Settings
    CART_ABANDONMENT_THRESHOLD_MINUTES = int(os.getenv("CART_ABANDONMENT_THRESHOLD", "30"))
    
    # Email Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "chanith2019@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "lpvdyufajsuahooe")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "chanith2019@gmail.com")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "8dbae9405f346aa4fe1aee65fb1f6223e5439079b9faf3ddad12610631bf88ff")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Frontend URLs
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ADMIN_URL = os.getenv("ADMIN_URL", "http://localhost:8000/admin")
    
    # AI Configuration
    AI_SETTINGS = {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    # Recovery Email Templates
    DEFAULT_EMAIL_TEMPLATES = {
        "subject_templates": [
            "Don't forget about your cart, {customer_name}!",
            "You left something behind, {customer_name}",
            "Complete your purchase and save!",
            "Your cart is waiting for you",
            "Still thinking about it, {customer_name}?"
        ],
        "offer_strategies": {
            "high_value": {  # Carts over $200
                "discount_percentage": 15,
                "free_shipping": True,
                "urgency_hours": 24
            },
            "medium_value": {  # Carts $50-$200
                "discount_percentage": 10,
                "free_shipping": True,
                "urgency_hours": 48
            },
            "low_value": {  # Carts under $50
                "discount_percentage": 5,
                "free_shipping": False,
                "urgency_hours": 72
            }
        }
    }
    
    # Monitoring and Analytics
    ANALYTICS_ENABLED = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_database_url(cls) -> str:
        return f"mysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}/{cls.DB_NAME}"
    
    @classmethod
    def get_openrouter_headers(cls) -> Dict[str, str]:
        return {
            "HTTP-Referer": cls.SITE_URL,
            "X-Title": cls.SITE_NAME,
            "Authorization": f"Bearer {cls.OPENROUTER_API_KEY}"
        }
