import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from config import Config
from database import DatabaseManager
from ai_agent import AIAgent

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class CartMonitoringService:
    def __init__(self):
        self.db = DatabaseManager()
        self.ai_agent = AIAgent(Config.OPENROUTER_API_KEY)
        self.running = False
    
    async def start_monitoring(self):
        """Start the cart monitoring service"""
        self.running = True
        # Ensure database connection
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return
            
        logger.info("Cart monitoring service started")
        
        while self.running:
            try:
                await self.check_abandoned_carts()
                await self.process_recovery_emails()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        logger.info("Cart monitoring service stopped")
    
    async def check_abandoned_carts(self):
        """Check for newly abandoned carts"""
        try:
            # Ensure database connection
            if not self.db.connection or not self.db.connection.is_connected():
                if not self.db.connect():
                    logger.error("Database connection failed")
                    return
                    
            # Get carts that haven't been updated in the threshold time
            abandoned_carts = self.db.get_abandoned_carts(
                minutes_threshold=Config.CART_ABANDONMENT_THRESHOLD_MINUTES
            )
            
            for cart in abandoned_carts:
                # Check if cart is already marked as abandoned
                if cart['status'] == 'active':
                    self.db.mark_cart_abandoned(cart['id'])
                    logger.info(f"Marked cart {cart['id']} as abandoned")
                    
                    # Schedule recovery email if user has email
                    if cart.get('email'):
                        await self.schedule_recovery_email(cart)
            
        except Exception as e:
            logger.error(f"Error checking abandoned carts: {e}")
    
    async def schedule_recovery_email(self, cart: Dict):
        """Schedule a recovery email for an abandoned cart"""
        try:
            cursor = self.db.connection.cursor()
            
            # Check if recovery email already sent
            cursor.execute("""
                SELECT COUNT(*) FROM recovery_attempts 
                WHERE cart_id = %s AND email_sent_at > NOW() - INTERVAL 24 HOUR
            """, (cart['id'],))
            
            if cursor.fetchone()[0] > 0:
                logger.info(f"Recovery email already sent for cart {cart['id']} in last 24h")
                return
            
            # Generate AI-powered email content
            email_content = self.ai_agent.generate_recovery_email(
                user_name=cart.get('name', 'Valued Customer'),
                cart_items=cart.get('items', 'your selected items'),
                cart_value=float(cart.get('total_value', 0))
            )
            
            # Generate personalized offer
            offer = self.ai_agent.suggest_offers(
                cart_items=cart.get('items', ''),
                cart_value=float(cart.get('total_value', 0))
            )
            
            # Save recovery attempt
            cursor.execute("""
                INSERT INTO recovery_attempts 
                (cart_id, email_subject, email_content, offer_type, offer_value)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                cart['id'],
                email_content['subject'],
                email_content['body'],
                offer['offer_type'],
                offer.get('offer_value', 0)
            ))
            
            recovery_id = cursor.lastrowid
            cursor.close()
            
            # Send email (if SMTP configured)
            if Config.SMTP_USER and Config.SMTP_PASSWORD:
                await self.send_recovery_email(cart, email_content, offer)
            
            logger.info(f"Recovery email scheduled for cart {cart['id']}")
            
        except Exception as e:
            logger.error(f"Error scheduling recovery email for cart {cart['id']}: {e}")
    
    async def send_recovery_email(self, cart: Dict, email_content: Dict, offer: Dict):
        """Send actual recovery email via SMTP"""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = Config.FROM_EMAIL
            msg['To'] = cart['email']
            msg['Subject'] = email_content['subject']
            
            # Add offer information to email body
            body_with_offer = email_content['body']
            if offer.get('offer_description'):
                body_with_offer += f"\n\nSpecial Offer: {offer['offer_description']}"
            
            # Add checkout link
            checkout_link = f"{Config.FRONTEND_URL}/checkout/{cart['id']}"
            body_with_offer += f"\n\nComplete your purchase: {checkout_link}"
            
            msg.attach(MIMEText(body_with_offer, 'plain'))
            
            # Send email
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(Config.FROM_EMAIL, cart['email'], text)
            server.quit()
            
            logger.info(f"Recovery email sent to {cart['email']} for cart {cart['id']}")
            
        except Exception as e:
            logger.error(f"Error sending recovery email: {e}")
    
    async def process_recovery_emails(self):
        """Process pending recovery emails and follow-ups"""
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            
            # Get recovery attempts that need follow-up
            cursor.execute("""
                SELECT ra.*, sc.total_value, u.email, 
                       CONCAT(u.first_name, ' ', u.last_name) as name
                FROM recovery_attempts ra
                JOIN shopping_carts sc ON ra.cart_id = sc.id
                LEFT JOIN users u ON sc.user_id = u.id
                WHERE ra.email_sent_at < NOW() - INTERVAL 24 HOUR
                AND ra.recovered = FALSE
                AND sc.status = 'abandoned'
            """)
            
            follow_up_attempts = cursor.fetchall()
            
            for attempt in follow_up_attempts:
                # Check if follow-up already sent
                cursor.execute("""
                    SELECT COUNT(*) FROM recovery_attempts 
                    WHERE cart_id = %s AND email_sent_at > %s
                """, (attempt['cart_id'], attempt['email_sent_at']))
                
                if cursor.fetchone()[0] == 0:  # No follow-up sent yet
                    await self.send_followup_email(attempt)
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error processing recovery emails: {e}")
    
    async def send_followup_email(self, original_attempt: Dict):
        """Send follow-up email with better offer"""
        try:
            # Generate more aggressive offer for follow-up
            improved_offer = self.ai_agent.suggest_offers(
                cart_items="previous cart items",
                cart_value=float(original_attempt['total_value']),
                user_history="abandoned cart - follow up"
            )
            
            # Increase offer value for follow-up
            if improved_offer['offer_type'] == 'percentage_discount':
                improved_offer['offer_value'] = min(improved_offer['offer_value'] + 5, 25)
            
            followup_email = self.ai_agent.generate_recovery_email(
                user_name=original_attempt.get('name', 'Valued Customer'),
                cart_items="your previous selection",
                cart_value=float(original_attempt['total_value'])
            )
            
            # Save follow-up attempt
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO recovery_attempts 
                (cart_id, email_subject, email_content, offer_type, offer_value, recovery_method)
                VALUES (%s, %s, %s, %s, %s, 'follow_up_email')
            """, (
                original_attempt['cart_id'],
                f"Last chance: {followup_email['subject']}",
                followup_email['body'],
                improved_offer['offer_type'],
                improved_offer.get('offer_value', 0)
            ))
            cursor.close()
            
            logger.info(f"Follow-up email scheduled for cart {original_attempt['cart_id']}")
            
        except Exception as e:
            logger.error(f"Error sending follow-up email: {e}")

# Global monitoring service instance
monitoring_service = CartMonitoringService()
