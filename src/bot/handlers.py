# Telegram Account Management Bot - Message Handlers
# All message and command handlers for the bot

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegram.ext import CallbackQueryHandler

from src.models.database import (
    get_or_create_user, get_user_accounts, get_user_countries,
    get_user_dates_for_country, get_user_accounts_by_date,
    delete_account, get_user_stats, get_user_proxies,
    add_proxy, delete_proxy, check_user_whitelisted,
    add_account as db_add_account
)
from src.utils.country import get_country_from_phone, is_valid_phone, normalize_phone_number
from src.bot.keyboards import (
    get_main_keyboard, get_accounts_keyboard, get_country_selection_keyboard,
    get_date_selection_keyboard, get_account_detail_keyboard, get_export_keyboard,
    get_proxy_keyboard, get_admin_keyboard, get_confirm_keyboard, get_country_emoji
)
from src.bot.states import States
from src.bot.callbacks import (
    show_accounts, select_country, select_date, show_account_detail,
    confirm_delete_account, export_menu, proxy_menu, proxy_add_start,
    proxy_delete_execute, admin_panel, admin_stats, admin_export_all,
    back_to_menu, cancel_operation, skip_2fa
)

logger = logging.getLogger(__name__)

# ============================================================================
# Command Handlers
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    
    # Check whitelist
    if not check_user_whitelisted(user.id):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "Your Telegram ID is not whitelisted to use this bot.\n"
            "Please contact the administrator for access.",
            parse_mode='Markdown'
        )
        return
    
    # Get or create user
    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Check if admin
    is_admin = user.id in [123456789, 987654321]  # Replace with actual admin IDs
    
    welcome_message = (
        f"👋 **Welcome, {user.first_name}!**\n\n"
        "I'm your **Telegram Account Manager** 🤖\n\n"
        "I can help you manage multiple Telegram accounts with:\n"
        "• 📱 **Add & Manage Accounts** - Add accounts with phone number\n"
        "• 🌍 **Country Detection** - Auto-detect country from phone\n"
        "• 📅 **Date Organization** - Accounts organized by date added\n"
        "• 🔒 **Proxy Support** - Use your own SOCKS5 proxies\n"
        "• 📦 **Bulk Export** - Export sessions for Telethon/Pyrogram\n"
        "• 📊 **Statistics** - View your account statistics\n\n"
        "Use the buttons below to get started!"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_keyboard(user.id, is_admin),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = (
        "📖 **Help Guide**\n\n"
        "**Adding Accounts:**\n"
        "1. Click '➕ Add Account'\n"
        "2. Enter phone number with country code (e.g., +1234567890)\n"
        "3. Enter the login code when prompted\n"
        "4. Enter 2FA password if enabled\n\n"
        
        "**Managing Accounts:**\n"
        "• Click '📱 My Accounts' to view all\n"
        "• Select a country to filter\n"
        "• Select a date to see accounts added on that day\n"
        "• Click an account to see details\n\n"
        
        "**Exporting Accounts:**\n"
        "• Click '📦 Bulk Export'\n"
        "• Choose export format (Telethon/Pyrogram)\n"
        "• Set the number of accounts to export\n\n"
        
        "**Proxy Management:**\n"
        "• Click '🔒 Proxy Manager'\n"
        "• Add your SOCKS5 proxy details\n"
        "• Proxies are saved for your account only\n\n"
        
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - View your statistics\n"
        "/accounts - List your accounts\n"
        "/export - Export accounts\n"
        "/proxy - Manage proxies"
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    user = update.effective_user
    
    # Check whitelist
    if not check_user_whitelisted(user.id):
        return
    
    stats = get_user_stats(user.id)
    
    if not stats or stats.get('total_accounts', 0) == 0:
        stats_text = "📊 **Your Statistics**\n\nYou haven't added any accounts yet!"
    else:
        stats_text = f"📊 **Your Statistics**\n\n"
        stats_text += f"📱 **Total Accounts:** {stats['total_accounts']}\n\n"
        
        stats_text += "🌍 **By Country:**\n"
        for country, count in stats.get('by_country', {}).items():
            stats_text += f"  • {country}: {count}\n"
        
        stats_text += "\n📅 **By Date:**\n"
        for date, count in list(stats.get('by_date', {}).items())[:5]:
            stats_text += f"  • {date}: {count}\n"
        
        if len(stats.get('by_date', {})) > 5:
            stats_text += f"  ... and {len(stats.get('by_date', {})) - 5} more dates"
    
    await update.message.reply_text(
        stats_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


# ============================================================================
# Account Management Handlers
# ============================================================================

async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start the account addition process"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📱 **Add New Account**\n\n"
        "Please enter the phone number with country code:\n"
        "Example: `+1234567890`\n\n"
        "Click 'Cancel' to go back.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]])
    )
    
    return States.PHONE


async def add_account_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle phone number input"""
    phone = update.message.text.strip()
    
    # Normalize and validate phone
    normalized_phone = normalize_phone_number(phone)
    
    if not is_valid_phone(normalized_phone):
        await update.message.reply_text(
            "❌ **Invalid Phone Number**\n\n"
            "Please enter a valid phone number with country code:\n"
            "Example: `+1234567890`\n\n"
            "Try again or click 'Cancel'.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]])
        )
        return States.PHONE
    
    # Get country info
    country_code, country_name, _ = get_country_from_phone(normalized_phone)
    
    if not country_code:
        await update.message.reply_text(
            "❌ **Unknown Country**\n\n"
            "Could not determine the country from the phone number.\n"
            "Please try again with a different format.",
            parse_mode='Markdown'
        )
        return States.PHONE
    
    # Store phone in context
    context.user_data['phone'] = normalized_phone
    context.user_data['country_code'] = country_code
    context.user_data['country_name'] = country_name
    
    emoji = get_country_emoji(country_code)
    
    await update.message.reply_text(
        f"{emoji} **Country Detected:** {country_name}\n\n"
        f"📱 **Phone:** {normalized_phone}\n\n"
        "Is this correct? If yes, I'll send a login code request to this number.\n\n"
        "Send 'yes' to continue or enter a different phone number.",
        parse_mode='Markdown'
    )
    
    return States.CODE


async def add_account_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle login code input"""
    response = update.message.text.strip().lower()
    
    if response in ['no', 'n', 'cancel']:
        await update.message.reply_text(
            "❌ **Cancelled**\n\n"
            "Enter the phone number again:",
            parse_mode='Markdown'
        )
        return States.PHONE
    
    # Simulate code request
    phone = context.user_data.get('phone')
    
    if phone:
        await update.message.reply_text(
            "📨 **Login Code Requested**\n\n"
            f"A login code has been sent to `{phone}`.\n\n"
            "Please enter the code you received.\n\n"
            "If the code doesn't arrive, you can:\n"
            "• Wait a few minutes\n"
            "• Try via SMS instead of call\n"
            "• Use a different number",
            parse_mode='Markdown'
        )
    
    return States.CODE


async def add_account_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 2FA password input"""
    await update.message.reply_text(
        "🔐 **Two-Factor Authentication**\n\n"
        "This account has 2FA enabled.\n"
        "Please enter your 2FA password.\n\n"
        "If you don't have one, click 'Skip'.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭️ Skip", callback_data="skip_2fa")
        ]])
    )
    
    return States.TWO_FA


# Aliases for backward compatibility
list_accounts = show_accounts
select_account = show_account_detail
delete_account = confirm_delete_account
export_bulk = export_menu
proxy_add = proxy_add_start
proxy_delete = proxy_delete_execute
admin_whitelist = admin_panel


# ============================================================================
# Utility Handlers
# ============================================================================

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation"""
    return await cancel_operation(update, context)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ **Unknown Command**\n\n"
        "I don't understand that command.\n"
        "Use /help to see available commands.",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling update: {context.error}")
    
    if update:
        await update.message.reply_text(
            "❌ **Error**\n\n"
            "An unexpected error occurred. Please try again later.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
