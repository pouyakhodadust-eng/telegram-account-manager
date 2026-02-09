"""
Telegram Account Manager - Main Bot Entry Point

A sophisticated Telegram bot for managing Telegram accounts with:
- Multi-user isolation
- Automatic country detection
- SOCKS5 proxy support
- Session file export (Telethon & Pyrogram)
- Glass-style UI
"""

import logging
from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from utils.config import config
from utils.country import get_country_info
from models.database import init_db, User
from bot.keyboards import get_main_keyboard

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, config.get("logging.level", "INFO")),
)
logger = logging.getLogger(__name__)


class TelegramAccountManagerBot:
    """
    Main bot class for Telegram Account Manager.
    
    Features:
    - Multi-user isolation
    - Account management with country/date categorization
    - Proxy support
    - Statistics
    - Session file delivery
    """
    
    def __init__(self):
        """Initialize the bot."""
        self.token = config.get("bot.token")
        self.api_id = config.get("bot.api_id")
        self.api_hash = config.get("bot.api_hash")
        
        if not self.token or not self.api_id or not self.api_hash:
            raise ValueError(
                "Missing required configuration: "
                "TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH"
            )
        
        self.app = (
            ApplicationBuilder()
            .token(self.token)
            .concurrent_updates(10)
            .build()
        )
        
        # Initialize database (not async, called before event loop starts)
        self._init_database()
        
        # Add handlers
        self._add_handlers()
    
    def _init_database(self) -> None:
        """Initialize the database."""
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    
    def _add_handlers(self) -> None:
        """Add all message and callback handlers."""
        
        # Command handlers
        self.app.add_handler(
            CommandHandler("start", self.handle_start)
        )
        self.app.add_handler(
            CommandHandler("help", self.handle_help)
        )
        self.app.add_handler(
            CommandHandler("menu", self.handle_menu)
        )
        
        # Message handlers
        self.app.add_handler(
            MessageHandler(
                filters.CONTACT,
                self.handle_contact
            )
        )
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_text
            )
        )
        
        # Callback query handler
        self.app.add_handler(
            CallbackQueryHandler(
                self.handle_callback
            )
        )
    
    async def handle_start(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle /start command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        user = update.effective_user
        
        logger.info(
            f"User {user.id} (@{user.username}) started the bot"
        )
        
        # Check if user is whitelisted
        allowed_users = config.get("bot.allowed_users", [])
        if allowed_users and str(user.id) not in allowed_users:
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator.",
            )
            return
        
        # Check if user exists in database
        # TODO: Implement user lookup from database
        
        welcome_text = (
            "🔐 **Welcome to Telegram Account Manager**\n\n"
            "Your trusted companion for managing Telegram accounts.\n\n"
            "✨ **Features:**\n"
            "• 📱 Store multiple Telegram accounts\n"
            "• 🌍 Automatic country detection\n"
            "• 📅 Organized by date added\n"
            "• 🔧 SOCKS5 proxy support\n"
            "• 📊 Detailed statistics\n"
            "• 📤 Deliver as session files\n\n"
            "Click the menu button below to get started!"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown",
        )
    
    async def handle_help(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle /help command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        help_text = (
            "ℹ️ **Help & Commands**\n\n"
            "**Main Commands:**\n"
            "/start - Start the bot\n"
            "/menu - Show main menu\n"
            "/help - Show this help\n\n"
            "**How to Use:**\n"
            "1️⃣ Click '➕ Add Account' to store a new account\n"
            "2️⃣ Enter the phone number\n"
            "3️⃣ Forward the login code\n"
            "4️⃣ Enter 2FA password if required\n\n"
            "**Delivery Options:**\n"
            "• Individual - Get login codes one by one\n"
            "• Bulk - Download session files (Telethon/Pyrogram)\n\n"
            "**Need Support?**\n"
            "Contact the administrator."
        )
        
        await update.message.reply_text(
            help_text,
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown",
        )
    
    async def handle_menu(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle /menu command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        await self.handle_callback_query(
            update.callback_query,
            "main_menu",
            context
        )
    
    async def handle_contact(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle contact messages (from phone number button).
        
        Args:
            update: Telegram update
            context: Callback context
        """
        contact = update.message.contact
        
        # Extract phone number from contact
        phone = contact.phone_number
        
        logger.info(f"Received contact: {phone}")
        
        # TODO: Implement account addition flow
        await update.message.reply_text(
            f"📱 Phone number received: {phone}\n\n"
            f"Detecting country...",
        )
        
        # Detect country
        country_info = get_country_info(phone)
        
        if country_info["is_valid"]:
            emoji = country_info.get("emoji", "🌍")
            await update.message.reply_text(
                f"{emoji} **Country Detected:** {country_info['country_name']}\n"
                f"📞 **Phone:** {phone}\n\n"
                f"Now send the login code to proceed.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ Could not detect country from this number.\n"
                "Please try again.",
            )
    
    async def handle_text(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle text messages.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        text = update.message.text
        
        logger.info(f"Received text: {text}")
        
        # TODO: Implement text handling for different states
        await update.message.reply_text(
            "I received your message. This is a placeholder.",
        )
    
    async def handle_callback(
        self, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """
        Handle callback queries from inline buttons.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        callback = update.callback_query
        await callback.answer()  # Close the loading state
        
        data = callback.data
        
        logger.info(f"Received callback: {data}")
        
        # Route to appropriate handler
        if data.startswith("country_"):
            await self.handle_country_callback(callback, data, context)
        elif data.startswith("date_"):
            await self.handle_date_callback(callback, data, context)
        elif data.startswith("account_"):
            await self.handle_account_callback(callback, data, context)
        elif data.startswith("delivery_"):
            await self.handle_delivery_callback(callback, data, context)
        elif data.startswith("proxy_"):
            await self.handle_proxy_callback(callback, data, context)
        elif data.startswith("stats_"):
            await self.handle_stats_callback(callback, data, context)
        else:
            await self.handle_general_callback(callback, data, context)
    
    async def handle_country_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle country-related callbacks."""
        if data == "countries_page_0":
            await callback.edit_message_text("🌍 Select a country:")
        else:
            await callback.edit_message_text(f"Selected country: {data}")
    
    async def handle_date_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle date-related callbacks."""
        await callback.edit_message_text(f"Selected date: {data}")
    
    async def handle_account_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle account-related callbacks."""
        await callback.edit_message_text(f"Selected account: {data}")
    
    async def handle_delivery_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle delivery-related callbacks."""
        await callback.edit_message_text(f"Delivery option: {data}")
    
    async def handle_proxy_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle proxy-related callbacks."""
        await callback.edit_message_text(f"Proxy option: {data}")
    
    async def handle_stats_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle statistics-related callbacks."""
        await callback.edit_message_text(f"Statistics: {data}")
    
    async def handle_general_callback(
        self,
        callback,
        data: str,
        context: CallbackContext
    ) -> None:
        """Handle general callbacks."""
        handlers = {
            "main_menu": ("🔐 Main Menu", "Select an option:"),
            "add_account": ("➕ Add Account", "Send the phone number to add:"),
            "accounts": ("👥 My Accounts", "Loading..."),
            "export_bulk": ("📤 Export Accounts", "Select export format:"),
            "stats": ("📊 Statistics", "Loading..."),
            "proxy_menu": ("🔧 Proxy Settings", "Select an option:"),
            "help": ("ℹ️ Help", "Use this bot to manage multiple Telegram accounts.\n\nFeatures:\n• Add accounts with phone numbers\n• View and manage accounts by country\n• Export sessions\n• Proxy support"),
        }
        
        if data in handlers:
            title, text = handlers[data]
            await callback.edit_message_text(
                f"**{title}**\n\n{text}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )
        else:
            await callback.edit_message_text(f"Callback: {data}")
    
    def run(self) -> None:
        """Start the bot."""
        logger.info("Starting Telegram Account Manager Bot...")
        
        # For python-telegram-bot v20+, use run_polling which handles everything
        self.app.run_polling()


async def handle_callback_query(
    callback,
    data: str,
    context: CallbackContext
) -> None:
    """
    Route callback queries to appropriate handlers.
    
    Args:
        callback: CallbackQuery object
        data: Callback data
        context: Callback context
    """
    bot = context.bot_data.get("bot")
    if bot:
        await bot.handle_callback(callback, data, context)


def main() -> None:
    """Main entry point."""
    # Create data directories
    Path("data/sessions").mkdir(parents=True, exist_ok=True)
    Path("data/exports").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    # Create and run the bot
    bot = TelegramAccountManagerBot()
    
    # Run the bot (run_polling handles its own event loop)
    bot.run()


if __name__ == "__main__":
    main()
