# Telegram Account Management Bot - Message Handlers
# All message and callback handlers for the bot

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from models.database import (
    get_or_create_user, get_user_accounts, get_user_countries,
    get_user_dates_for_country, get_user_accounts_by_date,
    delete_account, get_user_stats, get_user_proxies,
    add_proxy, delete_proxy, check_user_whitelisted,
    add_account as db_add_account
)
from utils.country import get_country_from_phone, is_valid_phone, normalize_phone_number
from bot.keyboards import (
    get_main_keyboard, get_accounts_keyboard, get_country_selection_keyboard,
    get_date_selection_keyboard, get_account_detail_keyboard, get_export_keyboard,
    get_proxy_keyboard, get_admin_keyboard, get_confirm_keyboard, get_country_emoji
)
from bot.states import States

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


async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List user's accounts"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "📱 **My Accounts**\n\n"
            "You haven't added any accounts yet!\n"
            "Click 'Add Account' to get started.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Add Account", callback_data="add_account"),
                InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
            ]])
        )
        return
    
    page = 1
    await query.edit_message_text(
        "📱 **My Accounts**\n\n"
        f"Total accounts: {len(accounts)}\n\n"
        "Select an account to view details:",
        parse_mode='Markdown',
        reply_markup=get_accounts_keyboard(accounts, page)
    )


async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select country for filtering accounts"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    countries = get_user_countries(user.id)
    
    if not countries:
        await query.edit_message_text(
            "🌍 **Select Country**\n\n"
            "You don't have any accounts yet!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Add Account", callback_data="add_account")
            ]])
        )
        return
    
    await query.edit_message_text(
        "🌍 **Select Country**\n\n"
        "Choose a country to filter your accounts:",
        parse_mode='Markdown',
        reply_markup=get_country_selection_keyboard(countries)
    )


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select date for filtering accounts within a country"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith('country_'):
        return
    
    country_code = data.replace('country_', '')
    
    user = update.effective_user
    countries = get_user_countries(user.id)
    
    country_name = "Unknown"
    for code, name in countries:
        if code == country_code:
            country_name = name
            break
    
    emoji = get_country_emoji(country_code)
    dates = get_user_dates_for_country(user.id, country_code)
    
    if not dates:
        await query.edit_message_text(
            f"{emoji} **{country_name}**\n\n"
            "No accounts found in this country!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 All Countries", callback_data="select_country")
            ]])
        )
        return
    
    await query.edit_message_text(
        f"{emoji} **{country_name}**\n\n"
        "Select a date to see accounts added on that day:",
        parse_mode='Markdown',
        reply_markup=get_date_selection_keyboard(dates, country_code)
    )


async def select_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select specific account from date filter"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith('date_'):
        return
    
    parts = data.replace('date_', '').split('_')
    country_code = parts[0]
    date_str = parts[1]
    
    user = update.effective_user
    accounts = get_user_accounts_by_date(
        user.id, country_code, 
        year=date_str.split('/')[0],
        month=date_str.split('/')[1],
        day=date_str.split('/')[2]
    )
    
    if not accounts:
        await query.edit_message_text(
            "📱 **No Accounts**\n\n"
            "No accounts found for this selection!",
            parse_mode='Markdown'
        )
        return
    
    account = accounts[0]
    emoji = get_country_emoji(account.country_code)
    
    await query.edit_message_text(
        f"{emoji} **{account.phone_number}**\n\n"
        f"🌍 **Country:** {account.country_name}\n"
        f"📅 **Added:** {account.added_date}\n"
        f"📤 **Login Code Forwards:** {account.login_code_forwards}\n"
        f"🔐 **Status:** {'Active' if account.is_active else 'Inactive'}",
        parse_mode='Markdown',
        reply_markup=get_account_detail_keyboard(account.id, country_code, date_str)
    )


async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete an account"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith('delete_'):
        return
    
    account_id = int(data.replace('delete_', ''))
    
    user = update.effective_user
    
    await query.edit_message_text(
        "⚠️ **Delete Account**\n\n"
        "Are you sure you want to delete this account?\n"
        "This action cannot be undone!\n\n"
        "Click 'Confirm' to delete or 'Cancel' to go back.",
        parse_mode='Markdown',
        reply_markup=get_confirm_keyboard("delete", account_id)
    )


# ============================================================================
# Export Handlers
# ============================================================================

async def export_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bulk export"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📦 **Bulk Export**\n\n"
        "Choose your export format:\n\n"
        "• **Telethon** - Export as `.session` files for Telethon\n"
        "• **Pyrogram** - Export as `.session` files for Pyrogram\n"
        "• **With Stats** - Include statistics in the export\n\n"
        "Select a format to continue:",
        parse_mode='Markdown',
        reply_markup=get_export_keyboard()
    )


# ============================================================================
# Proxy Handlers
# ============================================================================

async def proxy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show proxy management menu"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    proxies = get_user_proxies(user.id)
    
    if not proxies:
        await query.edit_message_text(
            "🔒 **Proxy Manager**\n\n"
            "You haven't added any proxies yet.\n\n"
            "Add a SOCKS5 proxy to use with your accounts.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Add Proxy", callback_data="proxy_add"),
                InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
            ]])
        )
        return
    
    await query.edit_message_text(
        "🔒 **Proxy Manager**\n\n"
        f"You have {len(proxies)} proxy(ies) configured.\n\n"
        "Select a proxy to manage:",
        parse_mode='Markdown',
        reply_markup=get_proxy_keyboard(proxies)
    )


async def proxy_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start proxy addition"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔒 **Add New Proxy**\n\n"
        "Please enter the proxy **host** (IP or domain):\n\n"
        "Example: `192.168.1.1` or `proxy.example.com`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="proxy_menu")
        ]])
    )
    
    return States.PROXY_HOST


async def proxy_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a proxy"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith('proxy_delete_'):
        return
    
    proxy_id = int(data.replace('proxy_delete_', ''))
    user = update.effective_user
    
    success = delete_proxy(user.id, proxy_id)
    
    if success:
        await query.answer("✅ Proxy deleted successfully!", show_alert=True)
    else:
        await query.answer("❌ Failed to delete proxy!", show_alert=True)
    
    await proxy_menu(update, context)


async def proxy_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all proxies"""
    await proxy_menu(update, context)


# ============================================================================
# Admin Handlers
# ============================================================================

async def admin_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage whitelist"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👥 **Whitelist Management**\n\n"
        "Manage which users can access this bot.",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show global statistics"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 **Global Statistics**\n\n"
        "This feature shows statistics for all users.",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


async def admin_export_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export all users' data"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📦 **Export All Users**\n\n"
        "Export all users' data in bulk.\n\n"
        "This may take a while for large datasets.",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


# ============================================================================
# Utility Handlers
# ============================================================================

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation"""
    query = update.callback_query
    
    if query:
        await query.answer()
        await query.edit_message_text(
            "❌ **Cancelled**\n\n"
            "Operation cancelled. What would you like to do next?",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ **Cancelled**\n\n"
            "Operation cancelled.",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()
    return ConversationHandler.END


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


# Import needed for conversation handler
from telegram.ext import ConversationHandler
from telegram import InlineKeyboardButton
