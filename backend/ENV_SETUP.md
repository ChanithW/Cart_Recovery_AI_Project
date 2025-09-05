# Environment Configuration

This project uses environment variables for secure configuration management.

## Setup Instructions

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual values:**

### Required Variables

- **OPENROUTER_API_KEY**: Your OpenRouter API key for AI services
  - Get one at: https://openrouter.ai/
  
- **SECRET_KEY**: A secure secret key for JWT tokens
  - Generate one using: `python -c "import secrets; print(secrets.token_hex(32))"`

### Email Configuration (Optional)

If you want to send recovery emails:

- **SMTP_USER**: Your email address
- **SMTP_PASSWORD**: Your email app password (for Gmail, use App Passwords)
- **FROM_EMAIL**: The "from" email address

### Database Configuration

- **DB_HOST**: MySQL host (default: localhost)
- **DB_USER**: MySQL username (default: root)
- **DB_PASSWORD**: MySQL password (leave empty if no password)
- **DB_NAME**: Database name (default: cart_recovery_ai)

## Security Notes

- **Never commit the `.env` file to version control**
- The `.env` file is included in `.gitignore`
- Use `.env.example` to share the required variables without exposing values
- Generate strong secret keys for production

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | - | OpenRouter API key for AI features |
| `SECRET_KEY` | ✅ Yes | - | JWT secret key (min 32 chars) |
| `DB_HOST` | No | localhost | MySQL database host |
| `DB_USER` | No | root | MySQL database user |
| `DB_PASSWORD` | No | (empty) | MySQL database password |
| `DB_NAME` | No | cart_recovery_ai | MySQL database name |
| `SMTP_USER` | No | - | Email SMTP username |
| `SMTP_PASSWORD` | No | - | Email SMTP password |
| `FROM_EMAIL` | No | - | From email address |
| `SITE_URL` | No | http://localhost:3000 | Site URL for AI context |
| `FRONTEND_URL` | No | http://localhost:3000 | Frontend URL |
