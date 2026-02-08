# Telegram Account Manager
## Multi-user Telegram account storage and management bot

### Features
- 📱 **Add Accounts** - Store Telegram accounts with automatic country detection
- 🌍 **Country Categories** - Accounts organized by phone number country code
- 📅 **Date Sub-categories** - Accounts grouped by addition date
- 🔐 **SOCKS5 Proxies** - Per-user proxy management to prevent bans
- 📊 **Statistics** - Detailed per-user account statistics
- 📤 **Delivery Methods** - Individual or bulk session file export
- 🔒 **Multi-user Isolation** - Each user sees only their own data
- ✨ **Glass UI** - Beautiful translucent button design

### Tech Stack
- **Python 3.11** - Core language
- **Telethon** - Telegram bot framework
- **PostgreSQL** - Metadata storage
- **Docker** - Containerized deployment

### Quick Start
```bash
# Clone and enter directory
cd telegram-account-manager

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start with Docker
docker-compose up -d

# Or run locally
pip install -r requirements.txt
python -m src.bot.main
```

### Environment Variables
See `.env.example` for all configuration options.

### Project Structure
```
telegram-account-manager/
├── config.yaml          # Main configuration
├── docker-compose.yml   # Docker services
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── README.md           # This file
├── src/
│   ├── bot/           # Bot handlers and keyboards
│   ├── utils/         # Helper utilities
│   └── models/        # Database models
└── data/
    ├── sessions/      # Telethon session files
    └── exports/       # ZIP exports
```

### License
MIT
