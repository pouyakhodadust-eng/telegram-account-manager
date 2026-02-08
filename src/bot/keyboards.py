"""
Telegram Account Manager - Glass-Style Keyboards

Beautiful translucent button designs for the Telegram bot.
"""

from typing import Optional

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove


# Glass effect constants
GLASS_BG_COLOR = "rgba(255, 255, 255, 0.1)"
GLASS_BORDER_COLOR = "rgba(255, 255, 255, 0.2)"
GLASS_TEXT_COLOR = "#FFFFFF"


def create_glass_button(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
) -> InlineKeyboardButton:
    """
    Create a glass-style inline button.
    
    Args:
        text: Button text (will have emoji automatically if not present)
        callback_data: Callback data for the button
        url: URL for URL buttons
        
    Returns:
        InlineKeyboardButton
    """
    # Add emoji if not present
    if not any(emoji in text for emoji in ["📱", "🔐", "📊", "📤", "🔧", "ℹ️", "⬅️", "✅", "❌"]):
        # Auto-add emoji based on text content
        if "add" in text.lower() or "new" in text.lower():
            text = "➕ " + text
        elif "delete" in text.lower() or "remove" in text.lower():
            text = "🗑️ " + text
        elif "edit" in text.lower() or "change" in text.lower():
            text = "✏️ " + text
        elif "view" in text.lower() or "show" in text.lower():
            text = "👁️ " + text
        elif "send" in text.lower() or "deliver" in text.lower():
            text = "📤 " + text
        elif "stat" in text.lower():
            text = "📊 " + text
        elif "proxy" in text.lower():
            text = "🔧 " + text
        elif "back" in text.lower() or "return" in text.lower():
            text = "⬅️ " + text
        elif "confirm" in text.lower():
            text = "✅ " + text
        elif "cancel" in text.lower():
            text = "❌ " + text
        elif "help" in text.lower() or "info" in text.lower():
            text = "ℹ️ " + text
    
    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data,
        url=url,
    )


class MainKeyboard:
    """Main menu keyboard with glass-style buttons."""
    
    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        """Get the main menu keyboard."""
        buttons = [
            [
                create_glass_button("➕ Add Account", callback_data="account_add"),
                create_glass_button("👥 My Accounts", callback_data="accounts_list"),
            ],
            [
                create_glass_button("📤 Deliver Accounts", callback_data="delivery_menu"),
                create_glass_button("📊 Statistics", callback_data="statistics"),
            ],
            [
                create_glass_button("🔧 Proxy Settings", callback_data="proxy_menu"),
                create_glass_button("ℹ️ Help", callback_data="help"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_empty_keyboard() -> InlineKeyboardMarkup:
        """Get empty keyboard when no accounts exist."""
        buttons = [
            [
                create_glass_button("➕ Add Your First Account", callback_data="account_add"),
            ],
            [
                create_glass_button("🔧 Proxy Settings", callback_data="proxy_menu"),
                create_glass_button("ℹ️ Help", callback_data="help"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)


class AccountKeyboard:
    """Account management keyboard."""
    
    @staticmethod
    def get_country_keyboard(
        countries: list[dict],
        page: int = 0,
        per_page: int = 5,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for country selection.
        
        Args:
            countries: List of country dicts with name, code, and account count
            page: Current page number
            per_page: Countries per page
        """
        # Filter out countries with zero accounts
        visible_countries = [c for c in countries if c.get("count", 0) > 0]
        
        if not visible_countries:
            buttons = [
                [
                    create_glass_button("⬅️ Back to Menu", callback_data="main_menu"),
                ],
            ]
            return InlineKeyboardMarkup(buttons)
        
        # Pagination
        start = page * per_page
        end = start + per_page
        page_countries = visible_countries[start:end]
        
        buttons = []
        for country in page_countries:
            emoji = country.get("emoji", "🌍")
            name = country.get("name", "Unknown")
            count = country.get("count", 0)
            button_text = f"{emoji} {name} ({count})"
            buttons.append([
                create_glass_button(
                    button_text,
                    callback_data=f"country_{country['code']}"
                )
            ])
        
        # Navigation buttons
        nav_buttons = []
        if start > 0:
            nav_buttons.append(
                create_glass_button("◀️ Prev", callback_data=f"countries_page_{page-1}")
            )
        if end < len(visible_countries):
            nav_buttons.append(
                create_glass_button("▶️ Next", callback_data=f"countries_page_{page+1}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        buttons.append([
            create_glass_button("⬅️ Back to Menu", callback_data="main_menu"),
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_date_keyboard(
        dates: list[dict],
        country_code: str,
        page: int = 0,
        per_page: int = 4,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for date selection within a country.
        
        Args:
            dates: List of date dicts with date string and account count
            country_code: Country code for back navigation
            page: Current page number
            per_page: Dates per page
        """
        # Filter out dates with zero accounts
        visible_dates = [d for d in dates if d.get("count", 0) > 0]
        
        buttons = []
        start = page * per_page
        end = start + per_page
        page_dates = visible_dates[start:end]
        
        for date_info in page_dates:
            date_str = date_info.get("date", "")
            count = date_info.get("count", 0)
            # Format date nicely
            formatted_date = format_date_nicely(date_str)
            button_text = f"📅 {formatted_date} ({count})"
            buttons.append([
                create_glass_button(
                    button_text,
                    callback_data=f"date_{date_str}_{country_code}"
                )
            ])
        
        # Navigation
        nav_buttons = []
        if start > 0:
            nav_buttons.append(
                create_glass_button("◀️ Prev", callback_data=f"dates_page_{page-1}_{country_code}")
            )
        if end < len(visible_dates):
            nav_buttons.append(
                create_glass_button("▶️ Next", callback_data=f"dates_page_{page+1}_{country_code}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Back buttons
        buttons.append([
            create_glass_button(
                "🌍 Change Country",
                callback_data=f"country_{country_code}_back"
            ),
            create_glass_button("⬅️ Menu", callback_data="main_menu"),
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_account_list_keyboard(
        accounts: list[dict],
        date_str: str,
        country_code: str,
        page: int = 0,
        per_page: int = 3,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for account selection.
        
        Args:
            accounts: List of account dicts with phone and status
            date_str: Date string for back navigation
            country_code: Country code for back navigation
            page: Current page number
            per_page: Accounts per page
        """
        buttons = []
        start = page * per_page
        end = start + per_page
        page_accounts = accounts[start:end]
        
        for account in page_accounts:
            phone = account.get("phone", "")
            masked_phone = mask_phone_number(phone)
            status = "✅" if account.get("is_logged_in") else "⏸️"
            button_text = f"{status} {masked_phone}"
            buttons.append([
                create_glass_button(
                    button_text,
                    callback_data=f"account_{account['id']}"
                )
            ])
        
        # Navigation
        nav_buttons = []
        if start > 0:
            nav_buttons.append(
                create_glass_button("◀️ Prev", callback_data=f"accounts_page_{page-1}_{date_str}")
            )
        if end < len(accounts):
            nav_buttons.append(
                create_glass_button("▶️ Next", callback_data=f"accounts_page_{page+1}_{date_str}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Back buttons
        buttons.append([
            create_glass_button(
                "📅 Change Date",
                callback_data=f"date_{date_str}_{country_code}_back"
            ),
            create_glass_button("🌍 Menu", callback_data="main_menu"),
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_account_actions_keyboard(
        account_id: int,
        phone: str,
        is_logged_in: bool,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for individual account actions.
        
        Args:
            account_id: Account ID
            phone: Masked phone number
            is_logged_in: Whether account is currently logged in
        """
        buttons = [
            [
                create_glass_button(
                    "📤 Deliver This Account",
                    callback_data=f"deliver_single_{account_id}"
                ),
            ],
        ]
        
        if is_logged_in:
            buttons.append([
                create_glass_button(
                    "🔄 Resend Code",
                    callback_data=f"resend_code_{account_id}"
                ),
                create_glass_button(
                    "🚪 Log Out",
                    callback_data=f"logout_{account_id}"
                ),
            ])
        
        buttons.append([
            create_glass_button(
                "⬅️ Back to List",
                callback_data=f"back_to_list_{account_id}"
            ),
        ])
        
        return InlineKeyboardMarkup(buttons)


class DeliveryKeyboard:
    """Delivery menu keyboard."""
    
    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        """Get the delivery menu keyboard."""
        buttons = [
            [
                create_glass_button(
                    "👤 Individual Delivery",
                    callback_data="delivery_individual"
                ),
            ],
            [
                create_glass_button(
                    "📦 Bulk Session Files",
                    callback_data="delivery_bulk"
                ),
            ],
            [
                create_glass_button("⬅️ Back to Menu", callback_data="main_menu"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_bulk_format_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for bulk export format selection."""
        buttons = [
            [
                create_glass_button(
                    "📄 Telethon Session",
                    callback_data="bulk_telethon"
                ),
            ],
            [
                create_glass_button(
                    "🐍 Pyrogram Session",
                    callback_data="bulk_pyrogram"
                ),
            ],
            [
                create_glass_button("⬅️ Back", callback_data="delivery_menu"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_logout_confirmation_keyboard(
        delivery_id: int,
        account_count: int,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for confirming logout after delivery.
        
        Args:
            delivery_id: Delivery session ID
            account_count: Number of accounts to log out
        """
        buttons = [
            [
                create_glass_button(
                    f"✅ Yes, Log Out ({account_count})",
                    callback_data=f"logout_delivered_{delivery_id}"
                ),
            ],
            [
                create_glass_button(
                    "❌ No, Keep Logged In",
                    callback_data="delivery_menu"
                ),
            ],
        ]
        return InlineKeyboardMarkup(buttons)


class StatisticsKeyboard:
    """Statistics display keyboard."""
    
    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        """Get the statistics menu keyboard."""
        buttons = [
            [
                create_glass_button(
                    "📱 Total Accounts",
                    callback_data="stats_total"
                ),
            ],
            [
                create_glass_button(
                    "🌍 By Country",
                    callback_data="stats_country"
                ),
            ],
            [
                create_glass_button(
                    "📅 By Date",
                    callback_data="stats_date"
                ),
            ],
            [
                create_glass_button(
                    "🔐 Active Sessions",
                    callback_data="stats_active"
                ),
            ],
            [
                create_glass_button("⬅️ Back to Menu", callback_data="main_menu"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)


class ProxyKeyboard:
    """Proxy settings keyboard."""
    
    @staticmethod
    def get_keyboard() -> InlineKeyboardMarkup:
        """Get the proxy menu keyboard."""
        buttons = [
            [
                create_glass_button(
                    "➕ Add New Proxy",
                    callback_data="proxy_add"
                ),
            ],
            [
                create_glass_button(
                    "📋 View My Proxies",
                    callback_data="proxy_list"
                ),
            ],
            [
                create_glass_button("⬅️ Back to Menu", callback_data="main_menu"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_proxy_list_keyboard(
        proxies: list[dict],
        page: int = 0,
        per_page: int = 2,
    ) -> InlineKeyboardMarkup:
        """
        Get keyboard for proxy list.
        
        Args:
            proxies: List of proxy dicts
            page: Current page
            per_page: Proxies per page
        """
        buttons = []
        start = page * per_page
        end = start + per_page
        page_proxies = proxies[start:end]
        
        for proxy in page_proxies:
            status = "✅" if proxy.get("is_verified") else "⏳"
            button_text = (
                f"{status} {proxy['host']}:{proxy['port']} "
                f"({proxy.get('country', '🌍')})"
            )
            buttons.append([
                create_glass_button(
                    button_text,
                    callback_data=f"proxy_{proxy['id']}"
                )
            ])
        
        # Navigation
        nav_buttons = []
        if start > 0:
            nav_buttons.append(
                create_glass_button("◀️ Prev", callback_data=f"proxy_page_{page-1}")
            )
        if end < len(proxies):
            nav_buttons.append(
                create_glass_button("▶️ Next", callback_data=f"proxy_page_{page+1}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        buttons.append([
            create_glass_button("➕ Add New Proxy", callback_data="proxy_add"),
            create_glass_button("⬅️ Menu", callback_data="main_menu"),
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_proxy_actions_keyboard(proxy_id: int) -> InlineKeyboardMarkup:
        """Get keyboard for individual proxy actions."""
        buttons = [
            [
                create_glass_button(
                    "✏️ Edit",
                    callback_data=f"proxy_edit_{proxy_id}"
                ),
                create_glass_button(
                    "🗑️ Delete",
                    callback_data=f"proxy_delete_{proxy_id}"
                ),
            ],
            [
                create_glass_button("⬅️ Back", callback_data="proxy_list"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)


class UserKeyboard:
    """User-related keyboards."""
    
    @staticmethod
    def get_approval_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
        """Get keyboard for admin to approve/reject user."""
        buttons = [
            [
                create_glass_button(
                    "✅ Approve",
                    callback_data=f"user_approve_{telegram_id}"
                ),
                create_glass_button(
                    "❌ Reject",
                    callback_data=f"user_reject_{telegram_id}"
                ),
            ],
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_phone_input_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for phone number input."""
        buttons = [
            [
                KeyboardButton("📱 Send Phone Number", request_contact=True),
            ],
        ]
        return ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Get cancel button keyboard."""
        buttons = [
            [
                create_glass_button("❌ Cancel", callback_data="cancel"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)


# Helper functions
def format_date_nicely(date_str: str) -> str:
    """
    Format a date string nicely.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Nicely formatted date (e.g., "February 24, 2026")
    """
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_str


def mask_phone_number(phone: str) -> str:
    """
    Mask a phone number for display.
    
    Args:
        phone: Full phone number
        
    Returns:
        Masked phone number (e.g., +1 *** *** 4567)
    """
    # Remove all non-digit characters
    digits = "".join(c for c in phone if c.isdigit())
    
    if len(digits) < 4:
        return phone
    
    # Keep first 2 and last 4 digits
    masked = (
        digits[:2] +
        " " +
        "*" * (len(digits) - 6) +
        " " +
        digits[-4:]
    )
    
    return f"+{masked}"
