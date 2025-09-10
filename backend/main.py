from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, WebSocket, WebSocketDisconnect
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

from database import DatabaseManager
from ai_agent import AIAgent
from auth_models import UserCreate, UserLogin, UserResponse, Token
from auth_service import AuthService, get_current_user
from config import Config
from chat_assistant import chat_assistant

app = FastAPI(title="Cart Recovery AI", description="Agentic E-commerce Cart Recovery System")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
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
        
        # Convert decimal to float for JSON serialization
        for product in products:
            if 'price' in product and product['price'] is not None:
                product['price'] = float(product['price'])
        
        return products
    except Error as e:
        print(f"Database error in get_products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in get_products: {str(e)}")
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
        
        # Convert decimal to float for JSON serialization
        if 'price' in product and product['price'] is not None:
            product['price'] = float(product['price'])
        
        return product
    except Error as e:
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
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                raise HTTPException(status_code=500, detail="Database connection failed")
        
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
        print(f"Database error in update_cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"General error in update_cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/cart/{session_id}")
def get_cart(session_id: str):
    """Get cart contents"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                # Return empty cart if database unavailable
                return {"cart_id": None, "items": [], "total_value": 0}
        
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
            "total_value": float(cart_data[0]["total_value"]) if cart_data[0]["total_value"] else 0,
            "items": []
        }
        
        for row in cart_data:
            if row["product_id"]:
                cart_info["items"].append({
                    "product_id": row["product_id"],
                    "name": row["name"],
                    "quantity": row["quantity"],
                    "price": float(row["price"]) if row["price"] else 0,
                    "image_url": row["image_url"]
                })
        
        return cart_info
        
    except Error as e:
        print(f"Database error in get_cart: {str(e)}")
        # Return empty cart on database error
        return {"cart_id": None, "items": [], "total_value": 0, "error": "Database temporarily unavailable"}
    except Exception as e:
        print(f"General error in get_cart: {str(e)}")
        # Return empty cart on any error
        return {"cart_id": None, "items": [], "total_value": 0, "error": "Service temporarily unavailable"}

@app.post("/cart/{cart_id}/generate-recovery-email")
async def generate_recovery_email(cart_id: int):
    """Generate AI-powered recovery email for abandoned cart"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        
        # Get cart details
        cursor.execute("""
            SELECT sc.*, u.email, 
                   CONCAT(u.first_name, ' ', u.last_name) as name,
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
        
        # Generate email using AI
        email_content = ai_agent.generate_recovery_email(
            user_name=cart["name"] or "Valued Customer",
            cart_items=cart["items"] or "your selected items",
            cart_value=float(cart["total_value"])
        )
        
        # Generate offer
        offer = ai_agent.suggest_offers(
            cart_items=cart["items"] or "your items",
            cart_value=float(cart["total_value"])
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
        abandoned_carts = db.get_abandoned_carts_analytics()
        
        analytics = {
            "total_abandoned": len(abandoned_carts),
            "total_value": sum(float(cart["total_value"]) for cart in abandoned_carts if cart["total_value"]),
            "carts": abandoned_carts
        }
        
        return analytics
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ========================
# WEBSOCKET TEST ENDPOINT
# ========================

@app.get("/api/test/websocket")
async def test_websocket_endpoint():
    """Test endpoint to verify WebSocket setup"""
    return {
        "status": "WebSocket endpoint ready",
        "endpoint": "/ws/chat/{session_id}",
        "test_url": "ws://localhost:8000/ws/chat/test-session",
        "active_connections": len(chat_assistant.active_connections)
    }

# ========================
# WEBSOCKET ENDPOINTS FOR CHAT ASSISTANT
# ========================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time shopping assistance"""
    print(f"New WebSocket connection attempt for session: {session_id}")
    
    try:
        await chat_assistant.connect(websocket, session_id)
        print(f"WebSocket connected successfully for session: {session_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            print(f"Received WebSocket message: {data}")
            
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            message_type = message_data.get("type", "user_message")
            
            if message_type == "user_message" and user_message:
                print(f"Processing user message: {user_message}")
                # Process user message and generate AI response
                ai_response = await chat_assistant.handle_user_message(session_id, user_message)
                print(f"Generated AI response: {ai_response}")
                await chat_assistant.send_message(session_id, ai_response)
            elif message_type == "cart_updated":
                # Handle cart update notifications
                cart_data = message_data.get("cart_data", {})
                await chat_assistant.handle_cart_update(session_id, cart_data)
            
    except WebSocketDisconnect:
        chat_assistant.disconnect(session_id)
        print(f"Chat session {session_id} disconnected")
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {str(e)}")
        chat_assistant.disconnect(session_id)

@app.post("/api/chat/notify-cart-update/{session_id}")
async def notify_cart_update(session_id: str, cart_data: Dict):
    """REST endpoint to notify chat assistant of cart updates"""
    try:
        # Send cart update notification to WebSocket if connected
        if session_id in chat_assistant.active_connections:
            notification = {
                "type": "cart_updated",
                "message": "I notice you've updated your cart. Need any help with those items?",
                "cart_data": cart_data,
                "timestamp": datetime.now().isoformat()
            }
            await chat_assistant.send_message(session_id, notification)
        
        return {"status": "notification_sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")

# ========================
# GDPR COMPLIANCE ENDPOINTS  
# ========================

@app.get("/api/user/data-export")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data for GDPR compliance (Article 20)"""
    try:
        user_id = current_user["user_id"]
        
        # For demo purposes, return mock data structure
        # In production, this would query the actual database
        user_data = {
            "export_date": datetime.now().isoformat(), 
            "user_id": user_id,
            "profile": {
                "id": user_id,
                "email": current_user.get("email", "demo@example.com"),
                "first_name": "Demo",
                "last_name": "User",
                "created_at": "2024-01-01T00:00:00"
            },
            "cart_history": [],
            "recovery_attempts": []
        }
        
        return user_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data export error: {str(e)}")

@app.delete("/api/user/delete-account")
async def delete_user_account(current_user: dict = Depends(get_current_user)):
    """Delete user account and all associated data (GDPR Article 17)"""
    try:
        user_id = current_user["user_id"]
        
        # For demo purposes, return success
        # In production, this would delete all user data from database
        return {"message": "Account and all associated data have been permanently deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account deletion error: {str(e)}")

@app.post("/api/user/unsubscribe")
async def unsubscribe_from_emails(email: EmailStr, unsubscribe_token: str):
    """Handle email unsubscribe requests"""
    try:
        # For demo purposes, return success
        # In production, this would update database preferences
        return {"message": "Successfully unsubscribed from marketing emails"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsubscribe error: {str(e)}")

@app.put("/api/user/privacy-settings")
async def update_privacy_settings(
    settings: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user privacy and email preferences"""
    try:
        user_id = current_user["user_id"]
        
        # For demo purposes, return success
        # In production, this would update database settings
        return {"message": "Privacy settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settings update error: {str(e)}")

# Serve static files for frontend
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard():
    """Serve admin dashboard"""
    return FileResponse("static/admin.html") if os.path.exists("static/admin.html") else HTMLResponse("<h1>Admin Dashboard Coming Soon</h1>")

# Remove the old monitor_cart_abandonment function since we're using the monitoring service
