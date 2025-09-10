from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import mysql.connector
from mysql.connector import Error
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
import os
import traceback

from database import DatabaseManager
from ai_agent import AIAgent
from auth_models import UserCreate, UserLogin, UserResponse, Token
from auth_service import AuthService, get_current_user
from config import Config

app = FastAPI(title="Cart Recovery AI", description="Agentic E-commerce Cart Recovery System")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
# Initialize AI agent with the API key from environment/config (do NOT hardcode keys in source)
ai_agent = AIAgent(api_key=Config.OPENROUTER_API_KEY)

# Pydantic models
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: str
    stock_quantity: int
    category: str

class CartItem(BaseModel):
    product_id: int
    quantity: int

class CartUpdate(BaseModel):
    user_id: Optional[int] = None
    session_id: str
    items: List[CartItem]

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = []
    session_id: str

class BehaviorTrackingRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: Optional[Dict] = None
    page_url: Optional[str] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set")
        raise
    
    db.create_database_and_tables()
    db.connect()
    # Start background task for cart abandonment detection
    from monitoring import monitoring_service
    asyncio.create_task(monitoring_service.start_monitoring())

@app.get("/")
def read_root():
    return {"message": "Cart Recovery AI Backend Running", "status": "active"}

@app.get("/products", response_model=List[ProductResponse])
def get_products():
    """Get all products"""
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE stock_quantity > 0")
        products = cursor.fetchall()
        cursor.close()
        # Defensive serialization: convert DECIMAL/bytearray types to native Python
        for p in products:
            # price may be Decimal or bytearray depending on connector/config
            if 'price' in p and p['price'] is not None:
                try:
                    p['price'] = float(p['price'])
                except Exception:
                    try:
                        # handle bytearray or other unexpected types
                        p['price'] = float(bytes(p['price']).decode())
                    except Exception:
                        p['price'] = None
        return products
    except Error as e:
        print(f"Database error in get_products: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in get_products: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a specific product"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Defensive serialization for single product
        if 'price' in product and product['price'] is not None:
            try:
                product['price'] = float(product['price'])
            except Exception:
                try:
                    product['price'] = float(bytes(product['price']).decode())
                except Exception:
                    product['price'] = None

        return product
    except Error as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Authentication Routes
@app.post("/auth/register", response_model=Token)
def register_user(user: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = AuthService.hash_password(user.password)
        
        # Create user
        user_id = db.create_user(user.email, user.first_name, user.last_name, password_hash)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Create access token
        access_token = AuthService.create_access_token(data={"sub": user.email})
        
        # Get user data for response
        user_data = db.get_user_by_id(user_id)
        user_response = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"]
        )
        
        return Token(access_token=access_token, token_type="bearer", user=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in register_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/login", response_model=Token)
def login_user(user_credentials: UserLogin):
    """Login user"""
    try:
        # Get user by email
        user = db.get_user_by_email(user_credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not AuthService.verify_password(user_credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token = AuthService.create_access_token(data={"sub": user["email"]})
        
        # Create user response
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
        
        return Token(access_token=access_token, token_type="bearer", user=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in login_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user_email: str = Depends(get_current_user)):
    """Get current user information"""
    try:
        user = db.get_user_by_email(current_user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user_info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/cart/update")
def update_cart(cart_data: CartUpdate):
    """Update shopping cart"""
    try:
        cursor = db.connection.cursor()
        
        # Find or create cart
        cursor.execute("""
            SELECT id FROM shopping_carts 
            WHERE (user_id = %s OR session_id = %s) AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (cart_data.user_id, cart_data.session_id))
        
        cart = cursor.fetchone()
        
        if cart:
            cart_id = cart[0]
            # Clear existing items
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
        else:
            # Create new cart
            cursor.execute("""
                INSERT INTO shopping_carts (user_id, session_id, status)
                VALUES (%s, %s, 'active')
            """, (cart_data.user_id, cart_data.session_id))
            cart_id = cursor.lastrowid
        
        # Add new items and calculate total
        total_value = 0
        for item in cart_data.items:
            # Get product price
            cursor.execute("SELECT price FROM products WHERE id = %s", (item.product_id,))
            product = cursor.fetchone()
            if product:
                price = float(product[0])
                cursor.execute("""
                    INSERT INTO cart_items (cart_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (cart_id, item.product_id, item.quantity, price))
                total_value += price * item.quantity
        
        # Update cart total
        cursor.execute("""
            UPDATE shopping_carts SET total_value = %s, updated_at = NOW()
            WHERE id = %s
        """, (total_value, cart_id))
        
        cursor.close()
        return {"cart_id": cart_id, "total_value": total_value, "message": "Cart updated successfully"}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/cart/{session_id}")
def get_cart(session_id: str):
    """Get cart contents"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        
        # Get cart with items
        cursor.execute("""
            SELECT sc.*, ci.product_id, ci.quantity, ci.price, p.name, p.image_url
            FROM shopping_carts sc
            LEFT JOIN cart_items ci ON sc.id = ci.cart_id
            LEFT JOIN products p ON ci.product_id = p.id
            WHERE sc.session_id = %s AND sc.status = 'active'
        """, (session_id,))
        
        cart_data = cursor.fetchall()
        cursor.close()
        
        if not cart_data:
            return {"cart_id": None, "items": [], "total_value": 0}
        
        cart_info = {
            "cart_id": cart_data[0]["id"],
            "total_value": float(cart_data[0]["total_value"]),
            "items": []
        }
        
        for row in cart_data:
            if row["product_id"]:
                cart_info["items"].append({
                    "product_id": row["product_id"],
                    "name": row["name"],
                    "quantity": row["quantity"],
                    "price": float(row["price"]),
                    "image_url": row["image_url"]
                })
        
        return cart_info
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/cart/{cart_id}/generate-recovery-email")
async def generate_recovery_email(cart_id: int):
    """Generate AI-powered recovery email for abandoned cart"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        
        # Get cart details
        cursor.execute("""
            SELECT sc.*, u.email,
                   GROUP_CONCAT(CONCAT(p.name, ' (', ci.quantity, ')') SEPARATOR ', ') as items
            FROM shopping_carts sc
            LEFT JOIN users u ON sc.user_id = u.id
            LEFT JOIN cart_items ci ON sc.id = ci.cart_id
            LEFT JOIN products p ON ci.product_id = p.id
            WHERE sc.id = %s
            GROUP BY sc.id
        """, (cart_id,))
        
        cart = cursor.fetchone()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Resolve user/display name safely (avoid assuming DB columns exist)
        user_name = None
        try:
            if cart.get('user_id'):
                user_row = db.get_user_by_id(cart.get('user_id'))
                if user_row:
                    # Prefer first/last name if present, else fall back to email
                    fn = user_row.get('first_name') if isinstance(user_row, dict) else None
                    ln = user_row.get('last_name') if isinstance(user_row, dict) else None
                    if fn or ln:
                        user_name = f"{fn or ''} {ln or ''}".strip()
                    else:
                        user_name = user_row.get('email') if isinstance(user_row, dict) else None
        except Exception:
            user_name = None

        if not user_name:
            user_name = cart.get('email') or 'Valued Customer'

        # Generate email using AI
        email_content = ai_agent.generate_recovery_email(
            user_name=user_name,
            cart_items=cart.get('items') or "your selected items",
            cart_value=float(cart.get('total_value') or 0)
        )
        
        # Generate offer using enhanced IR system
        offer = ai_agent.suggest_offers(
            cart_items=cart.get('items') or "your items",
            cart_value=float(cart.get('total_value') or 0),
            db_manager=db
        )
        
        # Save recovery attempt
        cursor.execute("""
            INSERT INTO recovery_attempts (cart_id, email_subject, email_content, offer_type, offer_value)
            VALUES (%s, %s, %s, %s, %s)
        """, (cart_id, email_content["subject"], email_content["body"], 
              offer["offer_type"], offer.get("offer_value", 0)))
        
        cursor.close()
        
        return {
            "email": email_content,
            "offer": offer,
            "cart_value": float(cart["total_value"]),
            "message": "Recovery email generated successfully"
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/analytics/abandoned-carts")
def get_abandoned_carts():
    """Get analytics on abandoned carts"""
    try:
        abandoned_carts = db.get_abandoned_carts(minutes_threshold=30)
        
        analytics = {
            "total_abandoned": len(abandoned_carts),
            "total_value": sum(float(cart["total_value"]) for cart in abandoned_carts),
            "carts": abandoned_carts
        }
        
        return analytics
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(chat_data: ChatMessage):
    """Conversational AI endpoint for customer support and product recommendations"""
    try:
        # Get session context (cart, user info if available)
        context_info = ""
        if chat_data.session_id:
            try:
                cursor = db.connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT sc.total_value, 
                           GROUP_CONCAT(CONCAT(p.name, ' (', ci.quantity, ')') SEPARATOR ', ') as cart_items
                    FROM shopping_carts sc
                    LEFT JOIN cart_items ci ON sc.id = ci.cart_id
                    LEFT JOIN products p ON ci.product_id = p.id
                    WHERE sc.session_id = %s AND sc.status = 'active'
                    GROUP BY sc.id
                """, (chat_data.session_id,))
                cart_info = cursor.fetchone()
                cursor.close()
                
                if cart_info and cart_info['cart_items']:
                    context_info = f"User has items in cart: {cart_info['cart_items']} (Total: ${float(cart_info['total_value']):.2f})"
            except Exception:
                context_info = ""
        
        # Build conversational prompt
        prompt = f"""
        You are a helpful e-commerce assistant for an online store. Answer the customer's question helpfully and naturally.
        
        Customer message: {chat_data.message}
        
        Context: {context_info or "No current cart items"}
        Additional context: {json.dumps(chat_data.context) if chat_data.context else "None"}
        
        Guidelines:
        - Be friendly and helpful
        - If they ask about products, suggest browsing our categories: Electronics, Sports, Home, Accessories
        - If they have cart items, you can reference them
        - If they ask about discounts/offers, mention we have cart recovery offers
        - Keep responses concise but informative
        - If you can't answer something specific, offer to help them find what they need
        
        Respond in a natural, conversational way. If appropriate, suggest 2-3 follow-up questions they might have.
        """
        
        try:
            completion = ai_agent.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "cart-recovery-ai.com",
                    "X-Title": "Cart Recovery AI",
                },
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful e-commerce customer service assistant. Be friendly, concise, and helpful."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            ai_reply = completion.choices[0].message.content
            
            # Generate simple follow-up suggestions based on the conversation
            suggestions = []
            message_lower = chat_data.message.lower()
            if "product" in message_lower or "buy" in message_lower:
                suggestions = ["What categories do you have?", "Do you have any deals?", "How do I checkout?"]
            elif "price" in message_lower or "cost" in message_lower:
                suggestions = ["Do you offer discounts?", "What about shipping costs?", "Any promo codes?"]
            elif "shipping" in message_lower:
                suggestions = ["How long does delivery take?", "Do you ship internationally?", "What's your return policy?"]
            else:
                suggestions = ["Tell me about your products", "Do you have customer support?", "How do I place an order?"]
            
        except Exception as e:
            # Fallback response if AI fails
            ai_reply = "I'm here to help you with your shopping! You can browse our products, ask about our current offers, or get help with your order. What would you like to know?"
            suggestions = ["Show me products", "Any current deals?", "Help with my cart"]
            print(f"Chat AI error: {e}")
        
        return ChatResponse(
            reply=ai_reply,
            suggestions=suggestions[:3],  # Limit to 3 suggestions
            session_id=chat_data.session_id or "anonymous"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.delete("/users/{user_id}/data")
def delete_user_data(user_id: int, anonymize_only: bool = True, current_user_email: str = Depends(get_current_user)):
    """GDPR: Delete or anonymize user data"""
    try:
        # Verify user can delete this data (admin or own data)
        current_user = db.get_user_by_email(current_user_email)
        target_user = db.get_user_by_id(user_id)
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only allow deletion of own data (or implement admin check)
        if current_user['id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot delete other user's data")
        
        success = db.delete_user_data(user_id, keep_anonymous=anonymize_only)
        
        if success:
            return {
                "message": f"User data {'anonymized' if anonymize_only else 'deleted'} successfully",
                "user_id": user_id,
                "anonymized": anonymize_only
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user data")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user data: {str(e)}")

@app.put("/users/{user_id}/preferences")
def update_user_preferences(
    user_id: int, 
    email_notifications: bool = True,
    marketing_emails: bool = True, 
    data_processing_consent: bool = True,
    current_user_email: str = Depends(get_current_user)
):
    """Update user preferences for GDPR compliance"""
    try:
        current_user = db.get_user_by_email(current_user_email)
        
        # Only allow updating own preferences
        if current_user['id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot update other user's preferences")
        
        pref_id = db.create_user_preferences(
            user_id=user_id,
            email_notifications=email_notifications,
            marketing_emails=marketing_emails,
            data_processing_consent=data_processing_consent
        )
        
        return {
            "message": "Preferences updated successfully",
            "preference_id": pref_id,
            "email_notifications": email_notifications,
            "marketing_emails": marketing_emails,
            "data_processing_consent": data_processing_consent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

@app.post("/behavior/track")
def track_behavior(request: BehaviorTrackingRequest):
    """Track user behavior for NLP abandonment analysis"""
    try:
        valid_events = ['page_view', 'product_view', 'cart_add', 'cart_remove', 'checkout_start', 'payment_attempt', 'exit_intent']
        
        if request.event_type not in valid_events:
            raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {valid_events}")
        
        behavior_id = db.track_user_behavior(
            session_id=request.session_id,
            event_type=request.event_type,
            event_data=request.event_data,
            page_url=request.page_url
        )
        
        return {
            "message": "Behavior tracked successfully",
            "behavior_id": behavior_id,
            "session_id": request.session_id,
            "event_type": request.event_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking behavior: {str(e)}")

@app.get("/behavior/analyze/{session_id}")
def analyze_abandonment_behavior(session_id: str):
    """Analyze user behavior for abandonment insights"""
    try:
        # Get behavior data
        behavior_data = db.get_user_behavior_pattern(session_id)
        
        # Get cart info for context
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT GROUP_CONCAT(CONCAT(p.name, ' (', ci.quantity, ')') SEPARATOR ', ') as items
            FROM shopping_carts sc
            LEFT JOIN cart_items ci ON sc.id = ci.cart_id
            LEFT JOIN products p ON ci.product_id = p.id
            WHERE sc.session_id = %s AND sc.status = 'active'
            GROUP BY sc.id
        """, (session_id,))
        cart_info = cursor.fetchone()
        cursor.close()
        
        cart_items = cart_info['items'] if cart_info else "No cart items"
        
        # Use enhanced NLP analysis
        analysis = ai_agent.analyze_abandonment_with_nlp(cart_items, behavior_data)
        
        return {
            "session_id": session_id,
            "behavior_events_count": len(behavior_data),
            "analysis": analysis,
            "cart_items": cart_items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing behavior: {str(e)}")

@app.get("/promotions/relevant")
def get_relevant_promotions(cart_value: float = 0, categories: Optional[str] = None):
    """Get relevant promotions using IR system"""
    try:
        category_list = categories.split(',') if categories else None
        promotions = db.get_relevant_promotions(
            cart_value=cart_value,
            categories=category_list
        )
        
        return {
            "promotions": promotions,
            "count": len(promotions),
            "cart_value": cart_value,
            "categories": category_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting promotions: {str(e)}")

# Serve static files for frontend
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard():
    """Serve admin dashboard"""
    return FileResponse("static/admin.html") if os.path.exists("static/admin.html") else HTMLResponse("<h1>Admin Dashboard Coming Soon</h1>")

# Remove the old monitor_cart_abandonment function since we're using the monitoring service
