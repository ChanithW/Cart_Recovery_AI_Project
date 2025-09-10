"""
Shopping Assistant Chatbot - Advanced Agentic AI Feature
Provides real-time conversational assistance for cart recovery and product recommendations
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from ai_agent import AIAgent
from config import Config

class ShoppingAssistant:
    def __init__(self):
        self.ai_agent = AIAgent(Config.OPENROUTER_API_KEY)
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and store session"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Send welcome message
        welcome_msg = await self.generate_welcome_message(session_id)
        await self.send_message(session_id, welcome_msg)
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: Dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                message_json = json.dumps(message)
                print(f"Sending message to {session_id}: {message_json}")
                await self.active_connections[session_id].send_text(message_json)
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                # Connection closed, remove it
                self.disconnect(session_id)
        else:
            print(f"No active connection found for session {session_id}")
    
    async def generate_welcome_message(self, session_id: str) -> Dict:
        """Generate personalized welcome message"""
        try:
            # Get user's current cart status
            cart_info = await self.get_session_cart_info(session_id)
            
            if cart_info and cart_info.get('items'):
                cart_value = cart_info.get('total_value', 0)
                item_count = len(cart_info.get('items', []))
                
                prompt = f"""
                Create a helpful welcome message for a shopping assistant chatbot.
                
                Context:
                - User has {item_count} items in cart
                - Cart value: ${cart_value:.2f}
                - Current session: Active shopping
                
                Create a friendly, helpful welcome that:
                1. Acknowledges their current cart
                2. Offers assistance with their shopping
                3. Mentions you can help with questions, recommendations, or checkout
                4. Keep it conversational and under 50 words
                
                Return JSON with: "message", "suggestions" (3 quick help options)
                """
            else:
                prompt = """
                Create a helpful welcome message for a shopping assistant chatbot.
                
                Context:
                - New visitor or empty cart
                - Ready to help with shopping
                
                Create a friendly welcome that:
                1. Introduces the assistant
                2. Offers help with product discovery
                3. Mentions available assistance types
                4. Keep it conversational and under 50 words
                
                Return JSON with: "message", "suggestions" (3 quick help options)
                """
            
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            welcome_data = json.loads(response.choices[0].message.content)
            welcome_data["type"] = "welcome"
            welcome_data["timestamp"] = datetime.now().isoformat()
            
            return welcome_data
            
        except Exception as e:
            return {
                "type": "welcome",
                "message": "Hi! I'm your shopping assistant. How can I help you today?",
                "suggestions": ["Show recommendations", "Check cart", "Find deals"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_user_message(self, session_id: str, user_message: str) -> Dict:
        """Process user message and generate AI response"""
        try:
            # Get user context
            cart_info = await self.get_session_cart_info(session_id)
            user_context = await self.get_user_context(session_id)
            
            # For testing, let's start with simple responses without AI
            # to ensure WebSocket connection works
            return await self.handle_simple_response(user_message, cart_info, session_id)
                
        except Exception as e:
            print(f"Error handling user message: {e}")
            return {
                "type": "error",
                "message": "I'm having trouble processing that. Could you try rephrasing?",
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_simple_response(self, message: str, cart_info: Dict, session_id: str) -> Dict:
        """Handle responses with simple logic (for testing)"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return {
                "type": "greeting",
                "message": "Hello! I'm your shopping assistant. How can I help you today?",
                "suggestions": ["Show recommendations", "Check my cart", "Find deals"],
                "timestamp": datetime.now().isoformat()
            }
        
        elif any(word in message_lower for word in ['cart', 'basket']):
            items_count = len(cart_info.get('items', [])) if cart_info else 0
            return {
                "type": "cart_assistance",
                "message": f"Your cart currently has {items_count} items. Would you like to see recommendations or check for deals?",
                "suggestions": ["Add more items", "Find similar products", "Check for discounts"],
                "timestamp": datetime.now().isoformat()
            }
        
        elif any(word in message_lower for word in ['recommend', 'suggest', 'show']):
            return {
                "type": "recommendations",
                "message": "Here are some popular products you might like:",
                "recommendations": [
                    {"name": "Premium Laptop", "reason": "Popular in electronics", "price_range": "$800-1200"},
                    {"name": "Wireless Headphones", "reason": "Great for music lovers", "price_range": "$100-300"},
                    {"name": "Smart Watch", "reason": "Trending tech accessory", "price_range": "$200-500"}
                ],
                "timestamp": datetime.now().isoformat()
            }
        
        elif any(word in message_lower for word in ['deal', 'discount', 'offer', 'sale']):
            return {
                "type": "discount_inquiry",
                "message": "Great question! Here are some current offers:",
                "offers": [
                    {"title": "New Customer Discount", "description": "Get 15% off your first order", "discount": "15% OFF"},
                    {"title": "Free Shipping", "description": "On orders over $50", "discount": "FREE SHIPPING"},
                    {"title": "Bundle Deal", "description": "Buy 2 get 10% off", "discount": "10% OFF"}
                ],
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            return {
                "type": "general",
                "message": "I understand you're asking about: \"" + message + "\". I'm here to help with your shopping! What would you like to know?",
                "suggestions": ["Show products", "Check deals", "Help with cart", "Product recommendations"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def classify_user_intent(self, message: str) -> str:
        """Classify user message intent using AI"""
        prompt = f"""
        Classify the user's shopping intent from this message: "{message}"
        
        Intent categories:
        - product_inquiry: Questions about specific products, features, comparisons
        - cart_assistance: Help with cart items, quantities, removal
        - recommendations: Want product suggestions or alternatives
        - discount_inquiry: Asking about deals, discounts, offers
        - checkout_help: Ready to purchase, payment questions
        - general_inquiry: General questions, greetings, other
        
        Return only the intent category name.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except:
            return "general_inquiry"
    
    async def handle_product_inquiry(self, message: str, cart_info: Dict, user_context: Dict) -> Dict:
        """Handle product-related questions"""
        prompt = f"""
        User is asking about products: "{message}"
        
        Cart context: {json.dumps(cart_info) if cart_info else "Empty cart"}
        User context: {json.dumps(user_context) if user_context else "New user"}
        
        Provide a helpful response that:
        1. Answers their product question
        2. Suggests relevant products if appropriate
        3. Mentions any related items in their cart
        4. Offers to help with comparisons or more details
        
        Return JSON with: "message", "product_suggestions" (if any), "next_actions"
        """
        
        response = await self.ai_agent.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        result["type"] = "product_inquiry"
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def handle_cart_assistance(self, message: str, cart_info: Dict) -> Dict:
        """Handle cart-related requests"""
        if not cart_info or not cart_info.get('items'):
            return {
                "type": "cart_assistance",
                "message": "Your cart is currently empty. Would you like me to show you some popular products?",
                "suggestions": ["Show trending items", "Browse categories", "Find deals"],
                "timestamp": datetime.now().isoformat()
            }
        
        items = cart_info.get('items', [])
        total_value = cart_info.get('total_value', 0)
        
        prompt = f"""
        User needs cart assistance: "{message}"
        
        Current cart:
        - Items: {len(items)}
        - Total value: ${total_value:.2f}
        - Items: {json.dumps(items)}
        
        Provide helpful cart assistance:
        1. Address their specific request
        2. Show current cart summary if relevant
        3. Suggest optimizations or related items
        4. Offer next steps
        
        Return JSON with: "message", "cart_summary", "suggestions"
        """
        
        response = await self.ai_agent.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        result["type"] = "cart_assistance"
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def handle_recommendations(self, cart_info: Dict, user_context: Dict) -> Dict:
        """Generate personalized product recommendations"""
        prompt = f"""
        Generate personalized product recommendations.
        
        Cart context: {json.dumps(cart_info) if cart_info else "Empty cart"}
        User context: {json.dumps(user_context) if user_context else "New user"}
        
        Provide 3-5 relevant recommendations:
        1. Based on cart items (complementary products)
        2. Based on popular items
        3. Based on seasonal trends
        4. Include reasons for each recommendation
        
        Return JSON with: "message", "recommendations" (array with name, reason, price_range)
        """
        
        response = await self.ai_agent.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        result["type"] = "recommendations"
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def handle_discount_inquiry(self, cart_info: Dict) -> Dict:
        """Handle discount and offer inquiries"""
        cart_value = cart_info.get('total_value', 0) if cart_info else 0
        
        # Use existing offer logic from ai_agent
        offers = await self.ai_agent.suggest_offers(cart_value, cart_info.get('items', []) if cart_info else [])
        
        return {
            "type": "discount_inquiry",
            "message": f"Great question! Based on your cart value of ${cart_value:.2f}, here are your available offers:",
            "offers": offers,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_checkout_assistance(self, cart_info: Dict) -> Dict:
        """Help with checkout process"""
        if not cart_info or not cart_info.get('items'):
            return {
                "type": "checkout_help",
                "message": "Your cart is empty. Add some items first, then I'll help you check out!",
                "suggestions": ["Browse products", "Show deals", "Popular items"],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "type": "checkout_help",
            "message": f"Ready to check out? Your cart has {len(cart_info.get('items', []))} items totaling ${cart_info.get('total_value', 0):.2f}",
            "cart_summary": cart_info,
            "next_steps": ["Review cart", "Apply discounts", "Proceed to checkout"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_general_inquiry(self, message: str, cart_info: Dict) -> Dict:
        """Handle general questions and conversation"""
        prompt = f"""
        User said: "{message}"
        
        Cart context: {"Has items" if cart_info and cart_info.get('items') else "Empty"}
        
        Provide a helpful, friendly response that:
        1. Addresses their message naturally
        2. Offers relevant shopping assistance
        3. Keeps the conversation focused on helping them shop
        4. Suggests useful next actions
        
        Return JSON with: "message", "suggestions"
        """
        
        response = await self.ai_agent.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        result = json.loads(response.choices[0].message.content)
        result["type"] = "general"
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def get_session_cart_info(self, session_id: str) -> Optional[Dict]:
        """Get cart information for session"""
        try:
            # For now, we'll simulate cart data
            # In production, you'd link session_id to user_id and get real cart
            return {
                "items": [],
                "total_value": 0,
                "session_id": session_id
            }
            
        except Exception as e:
            return None
    
    async def get_user_context(self, session_id: str) -> Optional[Dict]:
        """Get user context and preferences"""
        try:
            # In production, you'd get user's browsing history, preferences, etc.
            return {
                "session_id": session_id,
                "is_returning_user": False,
                "preferences": []
            }
        except Exception as e:
            return None
    
    async def handle_cart_update(self, session_id: str, cart_data: Dict):
        """Handle cart update notifications"""
        try:
            # Generate contextual message about cart update
            if cart_data.get('items'):
                item_count = len(cart_data.get('items', []))
                total_value = cart_data.get('total_value', 0)
                
                message = {
                    "type": "cart_update_response",
                    "message": f"I see you've updated your cart! You now have {item_count} item{'s' if item_count != 1 else ''} totaling ${total_value:.2f}. Need any help with those items?",
                    "suggestions": ["Get recommendations", "Check for deals", "Ready to checkout?"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                message = {
                    "type": "cart_update_response", 
                    "message": "I notice your cart is now empty. Would you like me to show you some popular products?",
                    "suggestions": ["Show trending items", "Browse categories", "Find deals"],
                    "timestamp": datetime.now().isoformat()
                }
            
            await self.send_message(session_id, message)
            
        except Exception as e:
            print(f"Error handling cart update: {e}")

# Global instance
chat_assistant = ShoppingAssistant()
