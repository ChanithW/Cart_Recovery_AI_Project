from openai import OpenAI
import json
from typing import List, Dict
import re
from datetime import datetime

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
    
    def suggest_offers(self, cart_items: str, cart_value: float, user_history: str = "", db_manager=None) -> Dict:
        """Generate personalized offers using AI + IR system"""
        
        # First, try to get relevant promotions from IR system
        relevant_promotions = []
        if db_manager:
            try:
                # Extract categories from cart items (simple keyword matching)
                categories = []
                if "headphone" in cart_items.lower() or "smartphone" in cart_items.lower() or "mouse" in cart_items.lower():
                    categories.append("Electronics")
                if "shoes" in cart_items.lower() or "yoga" in cart_items.lower():
                    categories.append("Sports")
                if "coffee" in cart_items.lower() or "backpack" in cart_items.lower():
                    categories.append("Home")
                
                relevant_promotions = db_manager.get_relevant_promotions(
                    cart_value=cart_value,
                    categories=categories if categories else None
                )
            except Exception as e:
                print(f"IR promotion retrieval error: {e}")
        
        prompt = f"""
        Create a personalized offer for a customer who abandoned their cart.
        
        Cart Details:
        - Items: {cart_items}
        - Value: ${cart_value:.2f}
        - Purchase History: {user_history or "New customer"}
        
        Available Promotions from our database:
        {json.dumps([{
            'name': p['name'], 
            'type': p['promotion_type'], 
            'value': float(p['discount_value']),
            'description': p['description'],
            'min_cart_value': float(p['min_cart_value'])
        } for p in relevant_promotions]) if relevant_promotions else "No specific promotions available"}
        
        Generate an appropriate offer considering:
        - Use available promotions if they fit the cart value and items
        - For carts over $200: 10-15% discount
        - For carts $100-200: 5-10% discount + free shipping
        - For carts under $100: Free shipping or small discount
        - Make the offer compelling and time-sensitive
        
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
                        "content": "You are an expert e-commerce strategist who creates compelling offers to recover abandoned carts. Use available promotions when appropriate. Always respond in valid JSON format."
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
                # Enhanced fallback logic using IR data
                if relevant_promotions:
                    best_promo = relevant_promotions[0]  # Highest priority
                    return {
                        "offer_type": best_promo['promotion_type'],
                        "offer_value": float(best_promo['discount_value']),
                        "offer_description": f"{best_promo['name']}: {best_promo['description']}"
                    }
                else:
                    # Original fallback
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
            # Try IR fallback first
            if relevant_promotions:
                best_promo = relevant_promotions[0]
                return {
                    "offer_type": best_promo['promotion_type'],
                    "offer_value": float(best_promo['discount_value']),
                    "offer_description": f"{best_promo['name']}: {best_promo['description']}"
                }
            return {
                "offer_type": "free_shipping",
                "offer_value": 0,
                "offer_description": "Free Shipping on your order!"
            }
    
    def analyze_abandonment_with_nlp(self, cart_items: str, behavior_data: List[Dict]) -> Dict:
        """Enhanced NLP abandonment analysis using behavior patterns"""
        
        # Analyze behavior patterns
        behavior_summary = self._analyze_behavior_patterns(behavior_data)
        
        prompt = f"""
        Analyze why a customer abandoned their cart using behavioral data and suggest recovery strategies.
        
        Cart Items: {cart_items}
        Behavior Pattern Analysis: {behavior_summary}
        
        Raw Behavior Events: {json.dumps(behavior_data[-10:]) if behavior_data else "No behavior data"}
        
        Analyze:
        1. Primary abandonment reasons based on behavior
        2. Customer intent level (high/medium/low)
        3. Best recovery timing (immediate/1hr/24hr/48hr)
        4. Recommended approach (discount/urgency/social proof/product focus)
        5. Likelihood of conversion (percentage)
        
        Return JSON with: "primary_reason", "intent_level", "recovery_timing_hours", "strategy", "conversion_likelihood"
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
                        "content": "You are an expert in e-commerce behavioral analytics and customer psychology. Provide actionable insights in JSON format."
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
                return self._fallback_analysis(behavior_summary)
                
        except Exception as e:
            print(f"Error in NLP abandonment analysis: {e}")
            return self._fallback_analysis(behavior_summary)
    
    def _analyze_behavior_patterns(self, behavior_data: List[Dict]) -> str:
        """Analyze behavior patterns to create summary"""
        if not behavior_data:
            return "No behavioral data available"
        
        events = [event['event_type'] for event in behavior_data]
        event_counts = {}
        for event in events:
            event_counts[event] = event_counts.get(event, 0) + 1
        
        # Time analysis
        if len(behavior_data) >= 2:
            session_duration = (
                datetime.fromisoformat(behavior_data[-1]['timestamp'].replace('Z', '+00:00')) -
                datetime.fromisoformat(behavior_data[0]['timestamp'].replace('Z', '+00:00'))
            ).total_seconds() / 60  # minutes
        else:
            session_duration = 0
        
        # Pattern analysis
        patterns = []
        if 'checkout_start' in events and 'payment_attempt' not in events:
            patterns.append("Started checkout but didn't attempt payment")
        if event_counts.get('product_view', 0) > 3:
            patterns.append("High product browsing activity")
        if 'exit_intent' in events:
            patterns.append("Showed exit intent")
        if session_duration > 10:
            patterns.append(f"Long session duration ({session_duration:.1f} minutes)")
        
        return f"Events: {event_counts}, Duration: {session_duration:.1f}min, Patterns: {patterns}"
    
    def _fallback_analysis(self, behavior_summary: str) -> Dict:
        """Fallback analysis when AI fails"""
        # Simple heuristic analysis
        if "checkout_start" in behavior_summary and "payment_attempt" not in behavior_summary:
            return {
                "primary_reason": "Payment hesitation",
                "intent_level": "high",
                "recovery_timing_hours": 1,
                "strategy": "Address payment concerns with security badges and easy checkout",
                "conversion_likelihood": 75
            }
        elif "exit_intent" in behavior_summary:
            return {
                "primary_reason": "Exit intent detected",
                "intent_level": "medium",
                "recovery_timing_hours": 2,
                "strategy": "Immediate popup offer or urgency messaging",
                "conversion_likelihood": 45
            }
        else:
            return {
                "primary_reason": "General browsing abandonment",
                "intent_level": "low",
                "recovery_timing_hours": 24,
                "strategy": "Educational content and gentle reminders",
                "conversion_likelihood": 25
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
