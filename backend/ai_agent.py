from openai import OpenAI
import json
from typing import List, Dict
import re

class AIAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    
    def generate_recovery_email(self, user_name: str, cart_items: str, cart_value: float) -> Dict:
        """Generate personalized cart recovery email using AI"""
        prompt = f"""
        Generate a compelling cart recovery email for an e-commerce customer. 
        
        Customer Details:
        - Name: {user_name}
        - Abandoned Items: {cart_items}
        - Cart Value: ${cart_value:.2f}
        
        Requirements:
        - Create an engaging subject line
        - Write a personalized email body that's friendly and persuasive
        - Include urgency without being pushy
        - Mention the specific items they left behind
        - Include a clear call-to-action
        - Keep it concise but compelling
        
        Format the response as JSON with keys: "subject" and "body"
        """
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "cart-recovery-ai.com",
                    "X-Title": "Cart Recovery AI",
                },
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email marketing specialist who creates compelling cart recovery emails that convert. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_content = completion.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if AI doesn't return proper JSON
                return {
                    "subject": f"Hey {user_name}, you left something behind!",
                    "body": f"Hi {user_name},\n\nWe noticed you left some great items in your cart: {cart_items}\n\nDon't miss out on these amazing products worth ${cart_value:.2f}!\n\nComplete your purchase now.\n\nBest regards,\nThe Team"
                }
                
        except Exception as e:
            print(f"Error generating email: {e}")
            return {
                "subject": f"Complete your purchase, {user_name}!",
                "body": f"Hi {user_name},\n\nYou have {cart_items} waiting in your cart. Complete your purchase now!\n\nTotal: ${cart_value:.2f}"
            }
    
    def suggest_offers(self, cart_items: str, cart_value: float, user_history: str = "") -> Dict:
        """Generate personalized offers using AI"""
        prompt = f"""
        Create a personalized offer for a customer who abandoned their cart.
        
        Cart Details:
        - Items: {cart_items}
        - Value: ${cart_value:.2f}
        - Purchase History: {user_history or "New customer"}
        
        Generate an appropriate offer that would encourage completion:
        - For carts over $200: 10-15% discount
        - For carts $100-200: 5-10% discount + free shipping
        - For carts under $100: Free shipping or small discount
        
        Consider:
        - The items in the cart
        - The total value
        - Customer history
        
        Return JSON with: "offer_type", "offer_value", "offer_description"
        """
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "cart-recovery-ai.com",
                    "X-Title": "Cart Recovery AI",
                },
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert e-commerce strategist who creates compelling offers to recover abandoned carts. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_content = completion.choices[0].message.content
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback offer logic
                if cart_value > 200:
                    return {
                        "offer_type": "percentage_discount",
                        "offer_value": 15,
                        "offer_description": "15% off your entire order!"
                    }
                elif cart_value > 100:
                    return {
                        "offer_type": "percentage_discount",
                        "offer_value": 10,
                        "offer_description": "10% off + Free Shipping!"
                    }
                else:
                    return {
                        "offer_type": "free_shipping",
                        "offer_value": 0,
                        "offer_description": "Free Shipping on your order!"
                    }
                    
        except Exception as e:
            print(f"Error generating offer: {e}")
            return {
                "offer_type": "free_shipping",
                "offer_value": 0,
                "offer_description": "Free Shipping on your order!"
            }
    
    def analyze_abandonment_reasons(self, cart_items: str, user_behavior: Dict) -> Dict:
        """Analyze potential reasons for cart abandonment"""
        prompt = f"""
        Analyze why a customer might have abandoned their cart and suggest strategies.
        
        Cart Items: {cart_items}
        User Behavior: {json.dumps(user_behavior)}
        
        Provide insights on:
        1. Likely abandonment reasons
        2. Recommended recovery strategy
        3. Best time to send recovery email
        
        Return JSON with: "reasons", "strategy", "timing_hours"
        """
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "cart-recovery-ai.com",
                    "X-Title": "Cart Recovery AI",
                },
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in e-commerce analytics and customer behavior. Provide actionable insights in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_content = completion.choices[0].message.content
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "reasons": ["Price comparison", "Unexpected shipping costs", "Distraction"],
                    "strategy": "Send personalized email with discount offer",
                    "timing_hours": 24
                }
                
        except Exception as e:
            print(f"Error analyzing abandonment: {e}")
            return {
                "reasons": ["Unknown"],
                "strategy": "Standard recovery email",
                "timing_hours": 24
            }
