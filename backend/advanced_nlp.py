"""
Advanced NLP Features for Agentic AI Cart Recovery System
Includes Named Entity Recognition, Sentiment Analysis, and User Journey Analysis
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ai_agent import AIAgent
from config import Config

class AdvancedNLP:
    def __init__(self, api_key: str):
        self.ai_agent = AIAgent(api_key)
    
    async def extract_shopping_entities(self, user_input: str, context: Dict = None) -> Dict:
        """
        Named Entity Recognition for shopping behavior
        Extracts products, categories, brands, price ranges, and features
        """
        prompt = f"""
        Analyze this shopping-related text and extract entities:
        Input: "{user_input}"
        Context: {json.dumps(context) if context else "None"}
        
        Extract and categorize entities:
        1. Products: Specific product names mentioned
        2. Categories: Product categories (electronics, clothing, etc.)
        3. Brands: Brand names mentioned
        4. Price_ranges: Any price or budget mentions
        5. Features: Product features or specifications
        6. Intent: Shopping intent (browsing, comparing, buying, etc.)
        7. Sentiment: Overall sentiment (positive, negative, neutral)
        8. Urgency: Level of purchase urgency (high, medium, low)
        
        Return JSON with these categories. Use null for empty categories.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            entities = json.loads(response.choices[0].message.content)
            entities["extraction_timestamp"] = datetime.now().isoformat()
            entities["input_text"] = user_input
            
            return entities
            
        except Exception as e:
            return {
                "error": f"Entity extraction failed: {str(e)}",
                "products": [],
                "categories": [],
                "brands": [],
                "price_ranges": [],
                "features": [],
                "intent": "unknown",
                "sentiment": "neutral",
                "urgency": "low"
            }
    
    async def analyze_abandonment_sentiment(self, user_behavior: Dict) -> Dict:
        """
        Analyze user's abandonment behavior for sentiment and reasons
        """
        prompt = f"""
        Analyze this user's cart abandonment behavior:
        
        Behavior Data:
        - Time spent on checkout page: {user_behavior.get('checkout_time', 0)} seconds
        - Cart modifications: {user_behavior.get('cart_changes', 0)} changes
        - Price comparison activities: {user_behavior.get('price_comparisons', 0)}
        - Exit page: {user_behavior.get('exit_page', 'unknown')}
        - Session duration: {user_behavior.get('session_duration', 0)} minutes
        - Previous purchases: {user_behavior.get('purchase_history', 0)}
        
        Determine:
        1. Primary abandonment reason (price, shipping, trust, comparison_shopping, technical_issues, distraction, undecided)
        2. Sentiment (frustrated, hesitant, comparison_shopping, price_sensitive, technical_difficulty)
        3. Recovery probability (high, medium, low)
        4. Recommended intervention strategy
        5. Optimal contact timing (immediate, 1hour, 24hours, 72hours)
        6. Personalization approach (discount, info, social_proof, urgency, reassurance)
        
        Return JSON with these insights.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["analysis_timestamp"] = datetime.now().isoformat()
            analysis["user_behavior"] = user_behavior
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Sentiment analysis failed: {str(e)}",
                "primary_reason": "unknown",
                "sentiment": "neutral",
                "recovery_probability": "medium",
                "intervention_strategy": "standard_email",
                "contact_timing": "24hours",
                "personalization_approach": "discount"
            }
    
    async def summarize_product_reviews(self, product_id: int, reviews_text: str) -> Dict:
        """
        Summarize product reviews for inclusion in cart recovery emails
        """
        prompt = f"""
        Summarize these product reviews for Product ID {product_id}:
        
        Reviews:
        {reviews_text}
        
        Create:
        1. Overall sentiment summary (2-3 sentences)
        2. Key positive points (top 3)
        3. Main concerns (if any, top 2)
        4. Star rating trend
        5. Reviewer confidence level (high/medium/low)
        6. Best use cases mentioned
        7. One compelling quote from reviews
        
        Keep summaries concise and marketing-friendly.
        Return JSON format.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            summary = json.loads(response.choices[0].message.content)
            summary["product_id"] = product_id
            summary["summary_timestamp"] = datetime.now().isoformat()
            
            return summary
            
        except Exception as e:
            return {
                "error": f"Review summarization failed: {str(e)}",
                "overall_sentiment": "Customers generally like this product",
                "positive_points": ["Good quality", "Fair price", "Fast delivery"],
                "main_concerns": [],
                "reviewer_confidence": "medium",
                "compelling_quote": "Great value for money!"
            }
    
    async def analyze_user_journey(self, session_events: List[Dict]) -> Dict:
        """
        Analyze user's shopping journey to identify hesitation signals and opportunities
        """
        # Convert events to readable format
        journey_text = "\n".join([
            f"{event.get('timestamp', '')}: {event.get('event_type', '')} - {event.get('details', '')}"
            for event in session_events
        ])
        
        prompt = f"""
        Analyze this user's shopping journey for behavioral patterns:
        
        Journey Events:
        {journey_text}
        
        Identify:
        1. Engagement level (high, medium, low)
        2. Decision confidence (confident, hesitant, confused)
        3. Price sensitivity signals
        4. Product research depth
        5. Comparison shopping behavior
        6. Abandonment risk factors
        7. Key hesitation moments
        8. Optimal intervention points
        9. Recommended next actions
        10. Personalization opportunities
        
        Return detailed JSON analysis.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["journey_timestamp"] = datetime.now().isoformat()
            analysis["event_count"] = len(session_events)
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Journey analysis failed: {str(e)}",
                "engagement_level": "medium",
                "decision_confidence": "hesitant",
                "abandonment_risk": "medium",
                "recommended_actions": ["send_email", "offer_discount"]
            }
    
    async def detect_purchase_intent(self, recent_behavior: Dict) -> Dict:
        """
        Detect user's purchase intent based on recent behavior patterns
        """
        prompt = f"""
        Analyze purchase intent from recent user behavior:
        
        Recent Activity:
        - Page views: {recent_behavior.get('page_views', [])}
        - Search queries: {recent_behavior.get('searches', [])}
        - Cart actions: {recent_behavior.get('cart_actions', [])}
        - Time patterns: {recent_behavior.get('session_times', [])}
        - Device/location: {recent_behavior.get('device_info', {})}
        
        Determine:
        1. Purchase intent score (0-100)
        2. Intent category (research, comparison, ready_to_buy, window_shopping)
        3. Likelihood to convert (high, medium, low)
        4. Best intervention strategy
        5. Optimal offer type
        6. Urgency level needed
        7. Preferred communication style
        8. Predicted purchase timeframe
        
        Return JSON with confidence scores.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            intent = json.loads(response.choices[0].message.content)
            intent["analysis_timestamp"] = datetime.now().isoformat()
            
            return intent
            
        except Exception as e:
            return {
                "error": f"Intent detection failed: {str(e)}",
                "purchase_intent_score": 50,
                "intent_category": "research",
                "conversion_likelihood": "medium",
                "intervention_strategy": "provide_information"
            }
    
    async def generate_personalized_subject_lines(self, user_profile: Dict, cart_data: Dict) -> List[str]:
        """
        Generate multiple personalized email subject lines using NLP insights
        """
        prompt = f"""
        Generate 5 personalized email subject lines for cart recovery:
        
        User Profile:
        - Name: {user_profile.get('name', 'Valued Customer')}
        - Purchase history: {user_profile.get('purchase_count', 0)} orders
        - Avg order value: ${user_profile.get('avg_order_value', 0):.2f}
        - Preferred categories: {user_profile.get('preferred_categories', [])}
        - Communication style: {user_profile.get('communication_style', 'friendly')}
        
        Cart Data:
        - Items: {len(cart_data.get('items', []))} products
        - Total value: ${cart_data.get('total_value', 0):.2f}
        - Top category: {cart_data.get('top_category', 'General')}
        - Abandonment time: {cart_data.get('time_since_abandon', 0)} hours ago
        
        Create subject lines that:
        1. Use personal elements (name, preferences)
        2. Create urgency without being pushy
        3. Highlight value proposition
        4. Match user's communication style
        5. Reference specific cart items when relevant
        
        Return JSON array of 5 subject lines with rationale for each.
        """
        
        try:
            response = await self.ai_agent.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return [
                {"subject": f"Don't miss out on your {cart_data.get('top_category', 'items')}, {user_profile.get('name', 'there')}!", "rationale": "Personalized with name and category"},
                {"subject": "Your cart is waiting – complete your order now", "rationale": "Simple urgency message"},
                {"subject": f"Save ${cart_data.get('total_value', 0):.2f} worth of great finds", "rationale": "Value-focused approach"},
                {"subject": "Almost yours – secure your items before they're gone", "rationale": "Scarcity-based motivation"},
                {"subject": "Ready to complete your purchase?", "rationale": "Gentle, question-based approach"}
            ]

# Global instance
advanced_nlp = AdvancedNLP(Config.OPENROUTER_API_KEY)
