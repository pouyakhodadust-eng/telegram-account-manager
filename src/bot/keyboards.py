# Telegram Account Management Bot - Glass-Style Keyboards
# Glass morphism / translucent button styles with emoji enhancements

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode

# Color palette for glass effect
GLASS_COLORS = {
    'background': 'rgba(30, 30, 46, 0.9)',      # Dark purple/gray
    'button': 'rgba(137, 180, 250, 0.3)',         # Soft blue
    'button_hover': 'rgba(166, 173, 200, 0.4)',   # Light gray-blue
    'accent': 'rgba(137, 180, 250, 1)',          # Bright blue
    'success': 'rgba(166, 227, 161, 1)',         # Green
    'danger': 'rgba(243, 139, 168, 1)',          # Red/Pink
    'warning': 'rgba(249, 226, 175, 1)',         # Yellow
    'info': 'rgba(116, 199, 236, 1)',            # Light blue
    'text': '#CDD6F4',                            # Light text
    'border': 'rgba(137, 180, 250, 0.5)',        # Border color
}

# Country emojis mapping
COUNTRY_EMOJIS = {
    'US': '🇺🇸', 'IR': '🇮🇷', 'RU': '🇷🇺', 'CN': '🇨🇳', 'IN': '🇮🇳',
    'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'CA': '🇨🇦', 'AU': '🇦🇺',
    'JP': '🇯🇵', 'KR': '🇰🇷', 'BR': '🇧🇷', 'MX': '🇲🇽', 'ID': '🇮🇩',
    'PH': '🇵🇭', 'VN': '🇻🇳', 'TH': '🇹🇭', 'MY': '🇲🇾', 'SG': '🇸🇬',
    'HK': '🇭🇰', 'TW': '🇹🇼', 'PK': '🇵🇰', 'BD': '🇧🇩', 'NG': '🇳🇬',
    'KE': '🇰🇪', 'EG': '🇪🇬', 'SA': '🇸🇦', 'AE': '🇦🇪', 'TR': '🇹🇷',
    'UA': '🇺🇦', 'PL': '🇵🇱', 'NL': '🇳🇱', 'BE': '🇧🇪', 'AT': '🇦🇹',
    'CH': '🇨🇭', 'SE': '🇸🇪', 'NO': '🇳🇴', 'DK': '🇩🇰', 'FI': '🇫🇮',
    'IE': '🇮🇪', 'PT': '🇵🇹', 'ES': '🇪🇸', 'IT': '🇮🇹', 'GR': '🇬🇷',
    'CZ': '🇨🇿', 'HU': '🇭🇺', 'RO': '🇷🇴', 'BG': '🇧🇬', 'RS': '🇷🇸',
    'HR': '🇭🇷', 'SK': '🇸🇰', 'LT': '🇱🇹', 'LV': '🇱🇻', 'EE': '🇪🇪',
    'BY': '🇧🇾', 'KZ': '🇰🇿', 'UZ': '🇺🇿', 'AZ': '🇦🇿', 'AM': '🇦🇲',
    'GE': '🇬🇪', 'NZ': '🇳🇿', 'ZA': '🇿🇦', 'AR': '🇦🇷', 'CL': '🇨🇱',
    'CO': '🇨🇴', 'PE': '🇵🇪', 'VE': '🇻🇪', 'EC': '🇪🇨', 'BO': '🇧🇴',
    'PY': '🇵🇾', 'UY': '🇺🇾', 'PA': '🇵🇦', 'CR': '🇨🇷', 'GT': '🇬🇹',
    'DO': '🇩🇴', 'PR': '🇵🇷', 'CU': '🇨🇺', 'JM': '🇯🇲', 'TT': '🇹🇹',
    'BB': '🇧🇧', 'BS': '🇧🇸', 'BM': '🇧🇲', 'KY': '🇰🇾', 'VG': '🇻🇬',
    'TC': '🇹🇨', 'AI': '🇦🇮', 'AG': '🇦🇬', 'DM': '🇩🇲', 'GD': '🇬🇩',
    'LC': '🇱🇨', 'VC': '🇻🇨', 'KN': '🇰🇳', 'MQ': '🇲🇶', 'RE': '🇷🇪',
    'YT': '🇾🇹', 'PF': '🇵🇫', 'NC': '🇳🇨', 'WF': '🇼🇫', 'FJ': '🇫🇯',
    'PG': '🇵🇬', 'SB': '🇸🇧', 'VU': '🇻🇺', 'TO': '🇹🇴', 'WS': '🇼🇸',
    'KI': '🇰🇮', 'NR': '🇳🇷', 'TV': '🇹🇻', 'PW': '🇵🇼', 'MH': '🇲🇭',
    'FM': '🇫🇲', 'TL': '🇹🇱', 'GQ': '🇬🇶', 'CG': '🇨🇬', 'CD': '🇨🇩',
    'AO': '🇦🇴', 'ZM': '🇿🇲', 'ZW': '🇿🇼', 'MW': '🇲🇼', 'MZ': '🇲🇿',
    'TZ': '🇹🇿', 'UG': '🇺🇬', 'RW': '🇷🇼', 'BI': '🇧🇮', 'SN': '🇸🇳',
    'CI': '🇨🇮', 'GH': '🇬🇭', 'TG': '🇹🇬', 'BJ': '🇧🇯', 'BF': '🇧🇫',
    'ML': '🇲🇱', 'NE': '🇳🇪', 'TD': '🇹🇩', 'CM': '🇨🇲', 'CF': '🇨🇫',
    'GA': '🇬🇦', 'GQ2': '🇬🇶', 'ST': '🇸🇹', 'CV': '🇨🇻', 'GN': '🇬🇳',
    'GM': '🇬🇲', 'SL': '🇸🇱', 'LR': '🇱🇷', 'SR': '🇸🇷', 'GY': '🇬🇾',
    'GF': '🇬🇫', 'MQ2': '🇲🇶', 'GL': '🇬🇱', 'FO': '🇫🇴', 'IS': '🇮🇸',
    'SJ': '🇸🇯', 'AX': '🇦🇽', 'GG': '🇬🇬', 'IM': '🇮🇲', 'JE': '🇯🇪',
    'MT': '🇲🇹', 'LU': '🇱🇺', 'MC': '🇲🇨', 'SM': '🇸🇲', 'VA': '🇻🇦',
    'AD': '🇦🇩', 'LI': '🇱🇮', 'AL': '🇦🇱', 'MK': '🇲🇰', 'ME': '🇲🇪',
    'BA': '🇧🇦', 'XK': '🇽🇰', 'FK': '🇫🇰', 'GS': '🇬🇸', 'TF': '🇹🇫',
    'HM': '🇭🇲', 'BV': '🇧🇻', 'AQ': '🇦🇶', 'CW': '🇨🇼', 'SX': '🇸🇽',
    'BQ': '🇧🇶', 'SS': '🇸🇸',
}


def get_country_emoji(country_code: str) -> str:
    """Get emoji for a country code"""
    return COUNTRY_EMOJIS.get(country_code, '🌐')


def create_glass_button(text: str, callback_data: str, emoji: str = None) -> InlineKeyboardButton:
    """Create a glass-style inline button with emoji"""
    display_text = f"{emoji} {text}" if emoji else text
    return InlineKeyboardButton(display_text, callback_data=callback_data)


def get_main_keyboard(telegram_id: int = None, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Get the main menu keyboard with glass-style buttons"""
    keyboard = [
        [
            create_glass_button("➕ Add Account", "add_account", "➕"),
            create_glass_button("📱 My Accounts", "accounts", "📱"),
        ],
        [
            create_glass_button("📊 Statistics", "stats", "📊"),
            create_glass_button("📦 Bulk Export", "export_bulk", "📦"),
        ],
        [
            create_glass_button("🔒 Proxy Manager", "proxy_menu", "🔒"),
            create_glass_button("❓ Help", "help", "❓"),
        ],
    ]
    
    # Add admin panel button for admins
    if is_admin:
        keyboard.append([
            create_glass_button("⚙️ Admin Panel", "admin_panel", "⚙️"),
        ])
    
    return InlineKeyboardMarkup(keyboard)


def get_accounts_keyboard(accounts, page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    """Get keyboard for account list with pagination"""
    keyboard = []
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_accounts = accounts[start_idx:end_idx]
    
    for i, account in enumerate(page_accounts):
        idx = start_idx + i + 1
        emoji = get_country_emoji(account.country_code)
        keyboard.append([
            create_glass_button(
                f"{emoji} {account.phone_number} ({account.added_date})",
                f"account_{account.id}",
                emoji
            )
        ])
    
    # Navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(create_glass_button("◀️ Prev", f"accounts_page_{page-1}", "◀️"))
    
    if end_idx < len(accounts):
        nav_row.append(create_glass_button("Next ▶️", f"accounts_page_{page+1}", "▶️"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Back button
    keyboard.append([
        create_glass_button("🔙 Back to Menu", "back_to_menu", "🔙")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_country_selection_keyboard(countries: list) -> InlineKeyboardMarkup:
    """Get keyboard for country selection (hides empty categories)"""
    keyboard = []
    
    for country_code, country_name in countries:
        emoji = get_country_emoji(country_code)
        keyboard.append([
            create_glass_button(
                f"{emoji} {country_name}",
                f"country_{country_code}",
                emoji
            )
        ])
    
    # Back button
    keyboard.append([
        create_glass_button("🔙 Back", "back_to_menu", "🔙")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_date_selection_keyboard(dates: list, country_code: str) -> InlineKeyboardMarkup:
    """Get keyboard for date selection within a country"""
    keyboard = []
    
    for date in dates:
        keyboard.append([
            create_glass_button(
                f"📅 {date}",
                f"date_{country_code}_{date}",
                "📅"
            )
        ])
    
    # Back button
    keyboard.append([
        create_glass_button("🔙 All Countries", "select_country", "🔙")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_account_detail_keyboard(account_id: int, country_code: str, date: str) -> InlineKeyboardMarkup:
    """Get keyboard for account detail actions"""
    keyboard = [
        [
            create_glass_button("📤 Forward Login Code", f"forward_{account_id}", "📤"),
            create_glass_button("📋 Copy Phone", f"copy_{account_id}", "📋"),
        ],
        [
            create_glass_button("🗑️ Delete Account", f"delete_{account_id}", "🗑️"),
        ],
        [
            create_glass_button("🔙 Back to Accounts", f"date_{country_code}_{date}", "🔙")
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for export options"""
    keyboard = [
        [
            create_glass_button("📤 Telethon (.session)", "export_telethon", "📤"),
            create_glass_button("📤 Pyrogram (.session)", "export_pyrogram", "📤"),
        ],
        [
            create_glass_button("📊 Export with Stats", "export_with_stats", "📊"),
            create_glass_button("🔙 Back to Menu", "back_to_menu", "🔙"),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_proxy_keyboard(proxies: list) -> InlineKeyboardMarkup:
    """Get keyboard for proxy management"""
    keyboard = []
    
    for proxy in proxies:
        keyboard.append([
            create_glass_button(
                f"🔒 {proxy.host}:{proxy.port}",
                f"proxy_edit_{proxy.id}",
                "🔒"
            )
        ])
    
    keyboard.append([
        create_glass_button("➕ Add New Proxy", "proxy_add", "➕")
    ])
    
    keyboard.append([
        create_glass_button("🔙 Back to Menu", "back_to_menu", "🔙")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for destructive actions"""
    keyboard = [
        [
            create_glass_button("✅ Confirm", f"confirm_{action}_{item_id}", "✅"),
            create_glass_button("❌ Cancel", "cancel", "❌"),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for admin panel"""
    keyboard = [
        [
            create_glass_button("👥 Manage Whitelist", "admin_whitelist", "👥"),
            create_glass_button("📊 Global Statistics", "admin_stats", "📊"),
        ],
        [
            create_glass_button("📦 Export All Users", "admin_export_all", "📦"),
            create_glass_button("🔙 Back to Menu", "back_to_menu", "🔙"),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_whitelist_keyboard(entries: list) -> InlineKeyboardMarkup:
    """Get keyboard for whitelist management"""
    keyboard = []
    
    for entry in entries:
        keyboard.append([
            create_glass_button(
                f"👤 {entry.telegram_id} ({entry.username or 'N/A'})",
                f"whitelist_{entry.telegram_id}",
                "👤"
            )
        ])
    
    keyboard.append([
        create_glass_button("➕ Add to Whitelist", "whitelist_add", "➕")
    ])
    
    keyboard.append([
        create_glass_button("🔙 Back to Admin", "admin_panel", "🔙")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_numeric_keyboard() -> ReplyKeyboardMarkup:
    """Get numeric keyboard for phone input"""
    keyboard = [
        [
            KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3"),
        ],
        [
            KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6"),
        ],
        [
            KeyboardButton("7"), KeyboardButton("8"), KeyboardButton("9"),
        ],
        [
            KeyboardButton("❌ Cancel"),
        ],
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def format_glass_message(title: str, content: str, emoji: str = None) -> str:
    """Format a message with glass-style markdown"""
    icon = f"{emoji} " if emoji else ""
    return f"{icon}**{title}**\n\n{content}"


def create_progress_bar(progress: int, total: int, length: int = 10) -> str:
    """Create a text-based progress bar"""
    filled = int(length * progress / total)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {progress}/{total}"
