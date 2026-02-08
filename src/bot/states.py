# Telegram Account Management Bot - Conversation States
# Define all conversation states for the bot

from enum import Enum


class States(Enum):
    """Conversation states for the bot"""
    
    # Main menu states
    MAIN_MENU = "main_menu"
    STATS_MENU = "stats_menu"
    EXPORT_MENU = "export_menu"
    PROXY_MENU = "proxy_menu"
    ADMIN_MENU = "admin_menu"
    
    # Account addition states
    ADD_ACCOUNT = "add_account"
    PHONE = "phone"
    CODE = "code"
    TWO_FA = "two_fa"
    
    # Account selection states
    SELECT_COUNTRY = "select_country"
    SELECT_DATE = "select_date"
    SELECT_ACCOUNT = "select_account"
    
    # Proxy management states
    PROXY_HOST = "proxy_host"
    PROXY_PORT = "proxy_port"
    PROXY_USERNAME = "proxy_username"
    PROXY_PASSWORD = "proxy_password"
    
    # Admin states
    ADMIN_WHITELIST_ADD = "admin_whitelist_add"
    ADMIN_WHITELIST_REMOVE = "admin_whitelist_remove"
    ADMIN_EXPORT = "admin_export"
    
    # Export states
    EXPORT_COUNT = "export_count"
    EXPORT_FORMAT = "export_format"
    
    # Confirmation states
    CONFIRM_DELETE = "confirm_delete"
    CONFIRM_EXPORT = "confirm_export"
    
    # Error states
    ERROR = "error"
    
    # Cancel state
    CANCEL = "cancel"


class CallbackPatterns:
    """Regex patterns for callback queries"""
    
    # Account patterns
    ACCOUNT_DETAIL = r"^account_(\d+)$"
    DELETE_ACCOUNT = r"^delete_(\d+)$"
    CONFIRM_DELETE = r"^confirm_delete_(\d+)$"
    
    # Country patterns
    COUNTRY_SELECT = r"^country_([A-Z]{2})$"
    DATE_SELECT = r"^date_([A-Z]{2})_(\d{4}/\d{2}/\d{2})$"
    
    # Pagination patterns
    ACCOUNTS_PAGE = r"^accounts_page_(\d+)$"
    
    # Export patterns
    EXPORT_TELETHON = r"^export_telethon$"
    EXPORT_PYROGRAM = r"^export_pyrogram$"
    EXPORT_WITH_STATS = r"^export_with_stats$"
    EXPORT_COUNT = r"^export_count_(\d+)$"
    
    # Proxy patterns
    PROXY_EDIT = r"^proxy_edit_(\d+)$"
    PROXY_DELETE = r"^proxy_delete_(\d+)$"
    
    # Admin patterns
    WHITELIST_USER = r"^whitelist_(\d+)$"
    WHITELIST_ADD = r"^whitelist_add$"
    WHITELIST_REMOVE = r"^whitelist_remove$"
    
    # Navigation patterns
    BACK_TO_MENU = r"^back_to_menu$"
    BACK_TO_ACCOUNTS = r"^back_to_accounts$"
    
    # Cancel pattern
    CANCEL = r"^cancel$"


# State descriptions for logging/debugging
STATE_DESCRIPTIONS = {
    States.MAIN_MENU: "User is in the main menu",
    States.STATS_MENU: "User is viewing statistics",
    States.EXPORT_MENU: "User is in export menu",
    States.PROXY_MENU: "User is managing proxies",
    States.ADMIN_MENU: "Admin is in admin panel",
    States.ADD_ACCOUNT: "User is adding a new account",
    States.PHONE: "Waiting for phone number input",
    States.CODE: "Waiting for login code input",
    States.TWO_FA: "Waiting for 2FA password input",
    States.SELECT_COUNTRY: "Selecting country for account",
    States.SELECT_DATE: "Selecting date for account",
    States.SELECT_ACCOUNT: "Selecting specific account",
    States.PROXY_HOST: "Entering proxy host",
    States.PROXY_PORT: "Entering proxy port",
    States.PROXY_USERNAME: "Entering proxy username",
    States.PROXY_PASSWORD: "Entering proxy password",
    States.ADMIN_WHITELIST_ADD: "Admin adding user to whitelist",
    States.ADMIN_WHITELIST_REMOVE: "Admin removing user from whitelist",
    States.ADMIN_EXPORT: "Admin exporting all data",
    States.EXPORT_COUNT: "Entering export count",
    States.EXPORT_FORMAT: "Selecting export format",
    States.CONFIRM_DELETE: "Confirming account deletion",
    States.CONFIRM_EXPORT: "Confirming export action",
    States.ERROR: "Error state",
    States.CANCEL: "Conversation cancelled",
}
