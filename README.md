# Cart Recovery AI - Complete E-commerce Solution

A full-stack agentic e-commerce website with AI-powered cart abandonment detection, personalized email generation, and intelligent offer suggestions using OpenRouter's DeepSeek API.

## 🚀 Features

### Core Features
- **Product Catalog**: Browse and search products with categories
- **Shopping Cart**: Add, remove, and update cart items
- **Cart Abandonment Detection**: AI monitors user behavior and detects abandoned carts
- **AI-Powered Email Generation**: DeepSeek API generates personalized recovery emails
- **Smart Offer Suggestions**: AI suggests contextual discounts and offers
- **Real-time Popup Notifications**: Instant abandonment alerts with offers
- **Admin Dashboard**: Monitor abandoned carts and recovery performance

### AI Agent Capabilities
- Personalized email subject lines and content
- Dynamic offer generation based on cart value and user behavior
- Abandonment reason analysis
- A/B testing for recovery strategies
- Behavioral pattern recognition

## 🛠 Technology Stack

### Backend
- **Python** with FastAPI
- **MySQL** database with phpMyAdmin
- **OpenRouter DeepSeek API** for AI capabilities
- **Pydantic** for data validation
- **SQLAlchemy** for database ORM

### Frontend
- **React** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API calls
- **Context API** for state management

### AI Integration
- **OpenRouter API** with DeepSeek Chat v3.1
- **Custom AI Agent** for email generation
- **Behavioral Analytics** for abandonment detection

## 📁 Project Structure

```
Cart_custom/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection and operations
│   ├── ai_agent.py          # AI agent for email/offer generation
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration settings
│   ├── monitoring.py        # Cart monitoring service
│   ├── requirements.txt     # Python dependencies
│   └── static/
│       └── admin.html       # Admin dashboard
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── context/         # Context providers
│   │   └── App.tsx          # Main application
│   ├── package.json         # Node.js dependencies
│   └── tailwind.config.js   # Tailwind configuration
└── database_schema.sql      # MySQL database schema
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- OpenRouter API Key

### 1. Database Setup
```sql
-- Import the database schema
mysql -u root -p < database_schema.sql
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Configure your API key in config.py
# Set OPENROUTER_API_KEY = "your-api-key-here"

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_db_password
DB_NAME=cart_recovery_ai

# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Site Configuration
SITE_URL=http://localhost:3000
SITE_NAME=Cart Recovery AI

# Email Settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@cartrecoveryai.com
```

### API Key Setup
1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Get your API key
3. Update `config.py` with your key

## 📊 API Endpoints

### Products
- `GET /products` - Get all products
- `GET /products/{id}` - Get specific product

### Cart Management
- `POST /cart/update` - Update cart items
- `GET /cart/{session_id}` - Get cart contents

### AI Features
- `POST /cart/{cart_id}/generate-recovery-email` - Generate AI recovery email
- `GET /analytics/abandoned-carts` - Get abandonment analytics

### User Management
- `POST /users/register` - Register new user

## 🤖 AI Agent Features

### Email Generation
The AI agent generates personalized recovery emails using:
- Customer name and purchase history
- Specific abandoned items
- Cart value and context
- Behavioral patterns

### Offer Suggestions
Smart offer generation based on:
- Cart value tiers (high/medium/low)
- Customer segment analysis
- Historical conversion data
- Seasonal trends

### Abandonment Analysis
AI analyzes abandonment reasons:
- Price sensitivity
- Shipping concerns
- Product hesitation
- Competition research

## 📈 Admin Dashboard

The admin dashboard provides:
- Real-time abandoned cart monitoring
- AI-generated email previews
- Recovery rate analytics
- Revenue impact tracking
- A/B testing results

## 🔄 Cart Monitoring Flow

1. **User Activity Tracking**: Monitor cart updates and page visits
2. **Abandonment Detection**: Detect when cart becomes inactive (30+ minutes)
3. **AI Analysis**: Analyze abandonment context and user behavior
4. **Email Generation**: Create personalized recovery content
5. **Offer Creation**: Generate contextual discount offers
6. **Delivery**: Send email or show popup notification
7. **Tracking**: Monitor open rates, clicks, and recoveries

## 🧪 Testing the System

### Test Cart Abandonment
1. Add products to cart
2. Wait 1-2 minutes (or adjust threshold in config)
3. Check admin dashboard for abandonment detection
4. View AI-generated recovery emails

### Test AI Features
1. Abandon different cart values to see varied offers
2. Try different product combinations
3. Monitor email generation quality
4. Test popup notifications

## 🛡 Security Features

- Input validation with Pydantic
- SQL injection prevention
- CORS configuration
- Rate limiting (can be added)
- Secure password hashing

## 📱 Mobile Responsive

The frontend is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices

## 🔮 Future Enhancements

- SMS recovery notifications
- WhatsApp integration
- Advanced A/B testing
- Machine learning for optimal timing
- Integration with email marketing platforms
- Advanced analytics dashboard
- Multi-language support
- Social media integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 💡 Tips for Success

1. **Monitor Analytics**: Regularly check the admin dashboard
2. **Test AI Responses**: Experiment with different cart scenarios
3. **Optimize Timing**: Adjust abandonment thresholds based on your audience
4. **Personalize Offers**: Use the AI's contextual offer suggestions
5. **Track Performance**: Monitor recovery rates and revenue impact

---

**Built with ❤️ using OpenRouter DeepSeek API and modern web technologies**
