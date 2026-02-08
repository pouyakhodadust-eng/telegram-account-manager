# Telegram Account Management Bot

A sophisticated Telegram Account Management Bot built with Python, Telethon, and PostgreSQL. Features a glass-morphism UI with emoji enhancements and comprehensive account management capabilities.

## Features

### Core Functionality
- 📱 **Multi-Account Management** - Add, view, and manage multiple Telegram accounts
- 🌍 **Auto Country Detection** - Automatically detect country from phone numbers
- 📅 **Date-Based Organization** - Accounts organized by date added (YYYY/MM/DD)
- 🔒 **User Data Isolation** - Each user sees only their own accounts
- 👥 **User Whitelist** - Admin-controlled access list

### Delivery Methods
- 📤 **Individual Forwarding** - Forward login codes to selected chats
- 📦 **Bulk Export** - Export sessions as ZIP for Telethon/Pyrogram

### Additional Features
- 🔌 **Proxy Management** - Per-user SOCKS5 proxy support
- 📊 **Statistics** - Per-user account statistics by country and date
- 🎨 **Glass UI** - Modern glass-morphism styled interface

## Tech Stack

- **Python 3.11** - Programming language
- **Telethon** - Telegram client library
- **PostgreSQL 15** - Database storage
- **SQLAlchemy** - ORM for database operations
- **Docker** - Containerized deployment

## Project Structure

```
telegram-account-manager/
├── config.yaml              # Configuration file
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Docker build file
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .env.example            # Environment template
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py         # Entry point
│   │   ├── handlers.py    # Message handlers
│   │   ├── keyboards.py    # UI keyboards
│   │   └── states.py      # Conversation states
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── country.py      # Phone country detection
│   │   ├── proxy.py       # Proxy management
│   │   ├── sessions.py    # Session export
│   │   └── dates.py       # Date handling
│   └── models/
│       ├── __init__.py
│       └── database.py    # PostgreSQL models
└── data/
    ├── sessions/          # Session files
    ├── exports/           # ZIP exports
    └── whitelist.txt      # User whitelist
```

## Installation

### Prerequisites
- Docker and Docker Compose
- PostgreSQL 15 (if running locally)
- Telegram Bot Token (from @BotFather)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram-account-manager
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the bot**
   ```bash
   docker-compose up -d
   ```

4. **Check logs**
   ```bash
   docker-compose logs -f bot
   ```

### Manual Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database**
   ```bash
   # Create PostgreSQL database
   psql -U postgres -c "CREATE DATABASE telegram_accounts;"
   ```

4. **Run the bot**
   ```bash
   python -m src.bot.main
   ```

## Configuration

### config.yaml

All configuration is managed through `config.yaml`:

```yaml
# Bot Configuration
bot:
  token: "${BOT_TOKEN}"  # Telegram Bot Token
  sessions_dir: "data/sessions"
  exports_dir: "data/exports"

# Database Configuration
database:
  host: "localhost"
  port: 5432
  username: "telegram_manager"
  password: "your_password"
  name: "telegram_accounts"
  table_prefix: "telegram_account_manager_"

# User Whitelist
whitelist:
  enabled: true
  admin_ids:
    - 123456789
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| BOT_TOKEN | Telegram Bot Token | Yes |
| DB_HOST | PostgreSQL host | No (default: localhost) |
| DB_PORT | PostgreSQL port | No (default: 5432) |
| DB_USER | PostgreSQL username | No |
| DB_PASSWORD | PostgreSQL password | No |
| DB_NAME | Database name | No |

## Usage

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/stats` | View your statistics |
| `/accounts` | List your accounts |
| `/export` | Export accounts |
| `/proxy` | Manage proxies |

### Adding Accounts

1. Click "➕ Add Account"
2. Enter phone number with country code (+1234567890)
3. Enter the login code received
4. Enter 2FA password if enabled

### Exporting Sessions

1. Click "📦 Bulk Export"
2. Choose format (Telethon/Pyrogram)
3. Set number of accounts to export
4. Download the ZIP file

## Database Schema

### Users Table
- `id` - Primary key
- `telegram_id` - Telegram user ID (unique)
- `username` - Telegram username
- `is_admin` - Admin status
- `is_whitelisted` - Whitelist status

### Telegram Accounts Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `phone_number` - Account phone number
- `country_code` - ISO country code
- `country_name` - Full country name
- `added_date` - Date added (YYYY-MM-DD)
- `session_file` - Session file path

### Proxies Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `host` - Proxy host
- `port` - Proxy port
- `username` - Proxy username (optional)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Security

- ⚠️ **Important**: Never share your bot token
- 🔐 **Data Isolation**: Each user's data is completely isolated
- 🚫 **Access Control**: User whitelist prevents unauthorized access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and feature requests, please open a GitHub issue.
