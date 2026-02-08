# Telegram Account Management Bot - Callback Query Handlers
# All inline button callback handlers with multi-user isolation

import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from src.models.database import (
    get_or_create_user, get_user_accounts, get_user_countries,
    get_user_dates_for_country, get_user_accounts_by_date,
    delete_account, get_user_stats, get_user_proxies,
    add_proxy, delete_proxy, check_user_whitelisted, add_account as db_add_account,
    get_user_by_telegram_id, get_user_accounts_by_country
)
from src.utils.country import get_country_from_phone, is_valid_phone, normalize_phone_number
from src.utils.sessions import export_sessions_zip, get_user_sessions, delete_session
from src.utils.dates import format_date_for_display, get_date_components
from src.bot.keyboards import (
    get_main_keyboard, get_accounts_keyboard, get_country_selection_keyboard,
    get_date_selection_keyboard, get_account_detail_keyboard, get_export_keyboard,
    get_proxy_keyboard, get_confirm_keyboard, get_country_emoji
)
from src.bot.states import States

logger = logging.getLogger(__name__)


# ============================================================================
# Callback Data Prefixes
# ============================================================================

class CallbackPrefixes:
    """Callback data prefixes for inline buttons"""
    ACCOUNT = "account_"
    DELETE = "delete_"
    CONFIRM_DELETE = "confirm_delete_"
    COUNTRY = "country_"
    DATE = "date_"
    PAGE = "accounts_page_"
    EXPORT = "export_"
    PROXY = "proxy_"
    PROXY_DELETE = "proxy_delete_"
    BACK = "back_"
    CANCEL = "cancel"
    SKIP = "skip_"


# ============================================================================
# Navigation Callbacks
# ============================================================================

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]  # Replace with actual admin IDs
    
    await query.edit_message_text(
        "📱 **Telegram Account Manager**\n\n"
        "Select an action from the menu below:",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id, is_admin)
    )


async def back_to_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to accounts list"""
    query = update.callback_query
    await query.answer()
    
    await list_accounts(update, context)


async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]
    
    await query.edit_message_text(
        "❌ **Cancelled**\n\n"
        "Operation cancelled. What would you like to do next?",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id, is_admin)
    )
    
    context.user_data.clear()
    return ConversationHandler.END


# ============================================================================
# Account Callbacks
# ============================================================================

async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's accounts list"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "📱 **My Accounts**\n\n"
            "You haven't added any accounts yet!\n\n"
            "Click 'Add Account' to get started.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    page = context.user_data.get('accounts_page', 1)
    
    await query.edit_message_text(
        f"📱 **My Accounts**\n\n"
        f"Total accounts: {len(accounts)}\n\n"
        "Select an account to view details:",
        parse_mode='Markdown',
        reply_markup=get_accounts_keyboard(accounts, page)
    )


async def show_account_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show account details"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.ACCOUNT):
        return
    
    account_id = int(query.data.replace(CallbackPrefixes.ACCOUNT, ''))
    user = update.effective_user
    
    accounts = get_user_accounts(user.id)
    account = next((a for a in accounts if a.id == account_id), None)
    
    if not account:
        await query.answer("❌ Account not found!", show_alert=True)
        return
    
    emoji = get_country_emoji(account.country_code)
    date_components = get_date_components(account.added_date)
    date_path = f"{date_components[0]}/{date_components[1]}/{date_components[2]}"
    
    await query.edit_message_text(
        f"{emoji} **{account.phone_number}**\n\n"
        f"🌍 **Country:** {account.country_name}\n"
        f"📅 **Added:** {format_date_for_display(account.added_date)}\n"
        f"📤 **Login Code Forwards:** {account.login_code_forwards}\n"
        f"🔐 **Status:** {'✅ Active' if account.is_active else '❌ Inactive'}",
        parse_mode='Markdown',
        reply_markup=get_account_detail_keyboard(account.id, account.country_code, date_path)
    )


async def pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination for account list"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.PAGE):
        return
    
    page = int(query.data.replace(CallbackPrefixes.PAGE, ''))
    context.user_data['accounts_page'] = page
    
    await show_accounts(update, context)


# ============================================================================
# Country & Date Callbacks
# ============================================================================

async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select country for filtering accounts"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    countries = get_user_countries(user.id)
    
    if not countries:
        await query.edit_message_text(
            "🌍 **Select Country**\n\n"
            "You don't have any accounts yet!\n\n"
            "Add an account first to see countries here.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
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
    
    if not query.data.startswith(CallbackPrefixes.COUNTRY):
        return
    
    country_code = query.data.replace(CallbackPrefixes.COUNTRY, '')
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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 All Countries", callback_data="select_country")]
            ])
        )
        return
    
    await query.edit_message_text(
        f"{emoji} **{country_name}**\n\n"
        "Select a date to see accounts added on that day:",
        parse_mode='Markdown',
        reply_markup=get_date_selection_keyboard(dates, country_code)
    )


async def filter_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Filter accounts by date"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.DATE):
        return
    
    parts = query.data.replace(CallbackPrefixes.DATE, '').split('_')
    country_code = parts[0]
    date_str = parts[1]
    
    user = update.effective_user
    date_components = date_str.split('/')
    accounts = get_user_accounts_by_date(
        user.id, country_code,
        year=date_components[0],
        month=date_components[1],
        day=date_components[2]
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
        f"📅 **Added:** {format_date_for_display(account.added_date)}\n"
        f"📤 **Login Code Forwards:** {account.login_code_forwards}\n"
        f"🔐 **Status:** {'✅ Active' if account.is_active else '❌ Inactive'}",
        parse_mode='Markdown',
        reply_markup=get_account_detail_keyboard(account.id, country_code, date_str)
    )


# ============================================================================
# Account Actions Callbacks
# ============================================================================

async def confirm_delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show delete confirmation for account"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.DELETE):
        return
    
    account_id = int(query.data.replace(CallbackPrefixes.DELETE, ''))
    
    await query.edit_message_text(
        "⚠️ **Delete Account**\n\n"
        "Are you sure you want to delete this account?\n\n"
        "⚠️ This will:\n"
        "• Remove the account from your list\n"
        "• Delete associated session files\n"
        "• This action cannot be undone!",
        parse_mode='Markdown',
        reply_markup=get_confirm_keyboard("delete", account_id)
    )


async def execute_delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute account deletion"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.CONFIRM_DELETE):
        return
    
    account_id = int(query.data.replace(CallbackPrefixes.CONFIRM_DELETE, ''))
    user = update.effective_user
    
    # Delete session file if exists
    accounts = get_user_accounts(user.id)
    account = next((a for a in accounts if a.id == account_id), None)
    
    if account and account.session_file:
        from pathlib import Path
        session_path = Path(account.session_file)
        if session_path.exists():
            delete_session(session_path)
    
    # Delete from database
    success = delete_account(user.id, account_id)
    
    if success:
        await query.answer("✅ Account deleted successfully!", show_alert=True)
        await show_accounts(update, context)
    else:
        await query.answer("❌ Failed to delete account!", show_alert=True)


async def copy_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Copy phone number to clipboard"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("copy_"):
        return
    
    account_id = int(query.data.replace("copy_", ''))
    user = update.effective_user
    
    accounts = get_user_accounts(user.id)
    account = next((a for a in accounts if a.id == account_id), None)
    
    if account:
        await query.answer(f"📱 {account.phone_number}", show_alert=True)


async def forward_login_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show login code forward options"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("forward_"):
        return
    
    account_id = int(query.data.replace("forward_", ''))
    
    await query.edit_message_text(
        "📤 **Forward Login Code**\n\n"
        "Configure where to forward login codes for this account.\n\n"
        "Coming soon!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data=f"account_{account_id}")]
        ])
    )


# ============================================================================
# Export Callbacks
# ============================================================================

async def export_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show export menu"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "📦 **Bulk Export**\n\n"
            "You don't have any accounts to export!\n\n"
            "Add some accounts first.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    await query.edit_message_text(
        "📦 **Bulk Export**\n\n"
        f"You have **{len(accounts)}** account(s) to export.\n\n"
        "Choose your export format:\n\n"
        "• **Telethon** - `.session` files for Telethon library\n"
        "• **Pyrogram** - `.session` files for Pyrogram library\n"
        "• **With Stats** - Include statistics file",
        parse_mode='Markdown',
        reply_markup=get_export_keyboard()
    )


async def export_telethon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export accounts in Telethon format"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "❌ **No Accounts**\n\n"
            "You don't have any accounts to export!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Get session files
    session_files = get_user_sessions(user.id)
    
    if not session_files:
        await query.edit_message_text(
            "⚠️ **No Session Files**\n\n"
            "No session files found for your accounts.\n\n"
            "Session files are created when you add accounts with valid login.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="export_bulk")]
            ])
        )
        return
    
    try:
        # Export sessions
        zip_path = export_sessions_zip(session_files, format='telethon', count=None)
        
        await query.edit_message_text(
            "✅ **Export Complete**\n\n"
            f"Exported **{len(session_files)}** session(s) in Telethon format.\n\n"
            f"📦 **File:** `{zip_path.name}`",
            parse_mode='Markdown'
        )
        
        # Send the file
        with open(zip_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=zip_path.name,
                caption=f"📦 Telethon Session Export\n\n"
                        f"Accounts: {len(session_files)}\n"
                        f"Format: Telethon (.session)"
            )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        await query.edit_message_text(
            f"❌ **Export Failed**\n\n"
            f"Error: {str(e)}",
            parse_mode='Markdown'
        )


async def export_pyrogram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export accounts in Pyrogram format"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "❌ **No Accounts**\n\n"
            "You don't have any accounts to export!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    session_files = get_user_sessions(user.id)
    
    if not session_files:
        await query.edit_message_text(
            "⚠️ **No Session Files**\n\n"
            "No session files found for your accounts.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="export_bulk")]
            ])
        )
        return
    
    try:
        zip_path = export_sessions_zip(session_files, format='pyrogram', count=None)
        
        await query.edit_message_text(
            "✅ **Export Complete**\n\n"
            f"Exported **{len(session_files)}** session(s) in Pyrogram format.",
            parse_mode='Markdown'
        )
        
        with open(zip_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=zip_path.name,
                caption=f"📦 Pyrogram Session Export\n\n"
                        f"Accounts: {len(session_files)}\n"
                        f"Format: Pyrogram (.session)"
            )
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        await query.edit_message_text(
            f"❌ **Export Failed**\n\n"
            f"Error: {str(e)}",
            parse_mode='Markdown'
        )


async def export_with_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export accounts with statistics"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    accounts = get_user_accounts(user.id)
    session_files = get_user_sessions(user.id)
    
    if not accounts:
        await query.edit_message_text(
            "❌ **No Accounts**\n\n"
            "You don't have any accounts to export!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    try:
        zip_path = export_sessions_zip(
            session_files if session_files else [],
            format='telethon',
            count=None,
            include_stats=True
        )
        
        stats = get_user_stats(user.id)
        
        await query.edit_message_text(
            "✅ **Export Complete**\n\n"
            f"Exported **{stats.get('total_accounts', 0)}** account(s) with statistics.",
            parse_mode='Markdown'
        )
        
        with open(zip_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=zip_path.name,
                caption=f"📊 Export with Statistics\n\n"
                        f"Accounts: {stats.get('total_accounts', 0)}\n"
                        f"Countries: {len(stats.get('by_country', {}))}"
            )
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        await query.edit_message_text(
            f"❌ **Export Failed**\n\n"
            f"Error: {str(e)}",
            parse_mode='Markdown'
        )


# ============================================================================
# Proxy Management Callbacks
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
            "SOCKS5 proxies can be used with your Telegram accounts.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Proxy", callback_data="proxy_add")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    await query.edit_message_text(
        "🔒 **Proxy Manager**\n\n"
        f"You have **{len(proxies)}** proxy(ies) configured.\n\n"
        "Select a proxy to manage:",
        parse_mode='Markdown',
        reply_markup=get_proxy_keyboard(proxies)
    )


async def proxy_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start adding a new proxy"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔒 **Add New Proxy**\n\n"
        "Please enter the proxy **host** (IP or domain):\n\n"
        "Example: `192.168.1.1` or `proxy.example.com`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="proxy_menu")]
        ])
    )
    
    context.user_data['adding_proxy'] = True


async def proxy_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit a proxy"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.PROXY):
        return
    
    proxy_id = int(query.data.replace(CallbackPrefixes.PROXY, ''))
    user = update.effective_user
    proxies = get_user_proxies(user.id)
    
    proxy = next((p for p in proxies if p.id == proxy_id), None)
    
    if not proxy:
        await query.answer("❌ Proxy not found!", show_alert=True)
        return
    
    auth_info = f"\n🔐 Auth: {proxy.username}@{proxy.password}" if proxy.username else ""
    
    await query.edit_message_text(
        f"🔒 **Proxy Details**\n\n"
        f"**Host:** `{proxy.host}`\n"
        f"**Port:** `{proxy.port}`{auth_info}\n"
        f"**Status:** {'✅ Active' if proxy.is_active else '❌ Inactive'}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ Delete", callback_data=f"{CallbackPrefixes.PROXY_DELETE}{proxy_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="proxy_menu")]
        ])
    )


async def proxy_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm proxy deletion"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(CallbackPrefixes.PROXY_DELETE):
        return
    
    proxy_id = int(query.data.replace(CallbackPrefixes.PROXY_DELETE, ''))
    
    await query.edit_message_text(
        "⚠️ **Delete Proxy**\n\n"
        "Are you sure you want to delete this proxy?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data=f"proxy_delete_confirm_{proxy_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="proxy_menu")]
        ])
    )


async def proxy_delete_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute proxy deletion"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("proxy_delete_confirm_"):
        return
    
    proxy_id = int(query.data.replace("proxy_delete_confirm_", ''))
    user = update.effective_user
    
    success = delete_proxy(user.id, proxy_id)
    
    if success:
        await query.answer("✅ Proxy deleted successfully!", show_alert=True)
    else:
        await query.answer("❌ Failed to delete proxy!", show_alert=True)
    
    await proxy_menu(update, context)


# ============================================================================
# Help Callback
# ============================================================================

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]
    
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
        "• Get your session files\n\n"
        
        "**Proxy Management:**\n"
        "• Click '🔒 Proxy Manager'\n"
        "• Add your SOCKS5 proxy details\n"
        "• Proxies are saved for your account only\n\n"
        
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - View your statistics"
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id, is_admin)
    )


# ============================================================================
# Statistics Callback
# ============================================================================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
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
        for date_str, count in list(stats.get('by_date', {}).items())[:5]:
            stats_text += f"  • {format_date_for_display(date_str)}: {count}\n"
        
        if len(stats.get('by_date', {})) > 5:
            stats_text += f"  ... and {len(stats.get('by_date', {})) - 5} more dates"
    
    user_obj = get_user_by_telegram_id(user.id)
    is_admin = user_obj.is_admin if user_obj else False
    
    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id, is_admin)
    )


# ============================================================================
# Skip Callbacks
# ============================================================================

async def skip_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Skip 2FA password input"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['skip_2fa'] = True
    
    await query.edit_message_text(
        "⏭️ **2FA Skipped**\n\n"
        "Continuing without 2FA password...",
        parse_mode='Markdown'
    )
    
    return States.CODE


# ============================================================================
# Admin Callbacks
# ============================================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]  # Replace with actual admin IDs
    
    if not is_admin:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    await query.edit_message_text(
        "⚙️ **Admin Panel**\n\n"
        "Welcome to the admin panel.\n\n"
        "Select an action:",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


async def admin_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage whitelist"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]
    
    if not is_admin:
        return
    
    await query.edit_message_text(
        "👥 **Whitelist Management**\n\n"
        "Manage which users can access this bot.\n\n"
        "Coming soon!",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show global statistics"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_admin = user.id in [123456789, 987654321]
    
    if not is_admin:
        return
    
    await query.edit_message_text(
        "📊 **Global Statistics**\n\n"
        "**Total Users:** 0\n"
        "**Total Accounts:** 0\n\n"
        "Coming soon!",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


# ============================================================================
# Callback Query Handler Setup
# ============================================================================

def get_callback_handlers() -> list:
    """
    Get all callback query handlers for registration.
    
    Returns:
        List of CallbackQueryHandler instances
    """
    handlers = [
        # Navigation
        CallbackQueryHandler(back_to_menu, pattern=r"^back_to_menu$"),
        CallbackQueryHandler(back_to_accounts, pattern=r"^back_to_accounts$"),
        CallbackQueryHandler(cancel_operation, pattern=r"^cancel$"),
        
        # Account list
        CallbackQueryHandler(show_accounts, pattern=r"^accounts$"),
        CallbackQueryHandler(show_account_detail, pattern=r"^account_\d+$"),
        CallbackQueryHandler(pagination_callback, pattern=r"^accounts_page_\d+$"),
        
        # Country & Date filtering
        CallbackQueryHandler(select_country, pattern=r"^select_country$"),
        CallbackQueryHandler(select_date, pattern=r"^country_[A-Z]{2}$"),
        CallbackQueryHandler(filter_by_date, pattern=r"^date_[A-Z]{2}_\d{4}/\d{2}/\d{2}$"),
        
        # Account actions
        CallbackQueryHandler(confirm_delete_account, pattern=r"^delete_\d+$"),
        CallbackQueryHandler(execute_delete_account, pattern=r"^confirm_delete_\d+$"),
        CallbackQueryHandler(copy_phone, pattern=r"^copy_\d+$"),
        CallbackQueryHandler(forward_login_code, pattern=r"^forward_\d+$"),
        
        # Export
        CallbackQueryHandler(export_menu, pattern=r"^export_bulk$"),
        CallbackQueryHandler(export_telethon, pattern=r"^export_telethon$"),
        CallbackQueryHandler(export_pyrogram, pattern=r"^export_pyrogram$"),
        CallbackQueryHandler(export_with_stats, pattern=r"^export_with_stats$"),
        
        # Proxy
        CallbackQueryHandler(proxy_menu, pattern=r"^proxy_menu$"),
        CallbackQueryHandler(proxy_add_start, pattern=r"^proxy_add$"),
        CallbackQueryHandler(proxy_edit, pattern=r"^proxy_edit_\d+$"),
        CallbackQueryHandler(proxy_delete_confirm, pattern=r"^proxy_delete_\d+$"),
        CallbackQueryHandler(proxy_delete_execute, pattern=r"^proxy_delete_confirm_\d+$"),
        
        # Help & Stats
        CallbackQueryHandler(show_help, pattern=r"^help$"),
        CallbackQueryHandler(show_stats, pattern=r"^stats$"),
        
        # Skip
        CallbackQueryHandler(skip_2fa, pattern=r"^skip_2fa$"),
        
        # Admin
        CallbackQueryHandler(admin_panel, pattern=r"^admin_panel$"),
        CallbackQueryHandler(admin_whitelist, pattern=r"^admin_whitelist$"),
        CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"),
        
        # Add account flow
        CallbackQueryHandler(lambda u, c: None, pattern=r"^add_account$"),
    ]
    
    return handlers
