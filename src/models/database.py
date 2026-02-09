# Telegram Account Management Bot - Database Models
# PostgreSQL models with row-level security for multi-user isolation

import os
import yaml
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Index, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.pool import QueuePool


# Load configuration
def load_config():
    """Load configuration from config.yaml"""
    # Try multiple possible locations for config.yaml
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml'),  # /app/config.yaml
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'),  # /app/src/config.yaml
        os.path.join(os.getcwd(), 'config.yaml'),  # cwd/config.yaml
    ]
    for config_path in possible_paths:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
    return {}


def _resolve_env(value, default=None):
    """Resolve ${VAR} placeholders in config values using environment variables."""
    if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
        env_var = value[2:-1]
        return os.environ.get(env_var, default)
    return value if value is not None else default


config = load_config()

# Database configuration
DB_CONFIG = config.get('database', {})
TABLE_PREFIX = _resolve_env(DB_CONFIG.get('table_prefix'), 'telegram_account_manager_')

# Database URL — resolve env var placeholders
db_user = _resolve_env(DB_CONFIG.get('username'), os.environ.get('DB_USER', 'telegram_manager'))
db_pass = _resolve_env(DB_CONFIG.get('password'), os.environ.get('DB_PASSWORD', 'secure_password'))
db_host = _resolve_env(DB_CONFIG.get('host'), os.environ.get('DB_HOST', 'localhost'))
db_port = _resolve_env(DB_CONFIG.get('port'), os.environ.get('DB_PORT', '5432'))
db_name = _resolve_env(DB_CONFIG.get('name'), os.environ.get('DB_NAME', 'telegram_accounts'))

DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================

class User(Base):
    """User model for storing user information"""
    __tablename__ = f"{TABLE_PREFIX}users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("TelegramAccount", back_populates="user", cascade="all, delete-orphan")
    proxies = relationship("Proxy", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class TelegramAccount(Base):
    """Telegram account model with date-based categorization"""
    __tablename__ = f"{TABLE_PREFIX}telegram_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{TABLE_PREFIX}users.id"), nullable=False, index=True)
    
    # Account information
    phone_number = Column(String(20), nullable=False, index=True)
    country_code = Column(String(10), nullable=False)  # ISO country code (US, IR, etc.)
    country_name = Column(String(100), nullable=False)
    
    # Date-based categorization (YYYY/MM/DD)
    added_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    added_year = Column(String(4), nullable=False)
    added_month = Column(String(2), nullable=False)
    added_day = Column(String(2), nullable=False)
    
    # Session file
    session_file = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    login_code_forwards = Column(Integer, default=0)  # Count of forwarded login codes
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index(f'ix_{TABLE_PREFIX}accounts_user_country', 'user_id', 'country_code'),
        Index(f'ix_{TABLE_PREFIX}accounts_user_date', 'user_id', 'added_year', 'added_month', 'added_day'),
        Index(f'ix_{TABLE_PREFIX}accounts_user_country_date', 'user_id', 'country_code', 'added_year', 'added_month', 'added_day'),
    )
    
    def __repr__(self):
        return f"<TelegramAccount(phone={self.phone_number}, country={self.country_code})>"


class Proxy(Base):
    """SOCKS5 proxy model for per-user proxy management"""
    __tablename__ = f"{TABLE_PREFIX}proxies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{TABLE_PREFIX}users.id"), nullable=False, index=True)
    
    # Proxy configuration
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(100), nullable=True)
    
    # Proxy metadata
    is_active = Column(Boolean, default=True)
    name = Column(String(100), nullable=True)  # Friendly name for the proxy
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="proxies")
    
    def __repr__(self):
        return f"<Proxy(host={self.host}, port={self.port})>"


class LoginCodeForward(Base):
    """Log of forwarded login codes for statistics"""
    __tablename__ = f"{TABLE_PREFIX}login_code_forwards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey(f"{TABLE_PREFIX}telegram_accounts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(f"{TABLE_PREFIX}users.id"), nullable=False, index=True)
    
    # Forward details
    forwarded_at = Column(DateTime, default=datetime.utcnow)
    target_chat_id = Column(String(50), nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<LoginCodeForward(account={self.account_id}, success={self.success})>"


class WhitelistEntry(Base):
    """Whitelist of approved Telegram user IDs"""
    __tablename__ = f"{TABLE_PREFIX}whitelist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    added_by = Column(String(50), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<WhitelistEntry(telegram_id={self.telegram_id})>"


# ============================================================================
# Database Operations
# ============================================================================

@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Load whitelist from file if exists
    load_whitelist_from_file()


def load_whitelist_from_file():
    """Load whitelist from config file"""
    # Try multiple possible locations for whitelist.txt
    possible_paths = [
        '/app/data/whitelist.txt',  # Docker mount path
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'whitelist.txt'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'whitelist.txt'),
    ]
    whitelist_path = None
    for p in possible_paths:
        if os.path.exists(p):
            whitelist_path = p
            break
    if whitelist_path is None:
        return
    
    with open(whitelist_path, 'r') as f:
        for line in f:
            telegram_id = line.strip()
            if telegram_id and telegram_id.isdigit():
                # Add to whitelist if not exists
                if not check_user_whitelisted(int(telegram_id)):
                    add_to_whitelist(int(telegram_id))


# ============================================================================
# User Operations
# ============================================================================

def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    """Get or create a user"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        
        if not user:
            user = User(
                telegram_id=str(telegram_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
                is_whitelisted=True
            )
            db.add(user)
            db.flush()
        
        return user


def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    with get_db() as db:
        return db.query(User).filter(User.telegram_id == str(telegram_id)).first()


def update_user(telegram_id: int, **kwargs) -> Optional[User]:
    """Update user information"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.flush()
        return user


# ============================================================================
# Account Operations (with user isolation)
# ============================================================================

def add_account(
    user_id: int,
    phone_number: str,
    country_code: str,
    country_name: str,
    added_date: str = None,
    added_year: str = None,
    added_month: str = None,
    added_day: str = None,
    session_file: str = None
) -> TelegramAccount:
    """Add a new Telegram account for a user"""
    with get_db() as db:
        # Get user
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        if not user:
            raise ValueError(f"User with telegram_id {user_id} not found")
        
        # Set date if not provided
        if added_date is None:
            now = datetime.utcnow()
            added_date = now.strftime('%Y-%m-%d')
            added_year = str(now.year)
            added_month = str(now.month).zfill(2)
            added_day = str(now.day).zfill(2)
        
        account = TelegramAccount(
            user_id=user.id,
            phone_number=phone_number,
            country_code=country_code,
            country_name=country_name,
            added_date=added_date,
            added_year=added_year,
            added_month=added_month,
            added_day=added_day,
            session_file=session_file
        )
        
        db.add(account)
        db.flush()
        return account


def get_user_accounts(telegram_id: int) -> List[TelegramAccount]:
    """Get all accounts for a user (data isolation)"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        return db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        ).all()


def get_user_accounts_by_country(telegram_id: int, country_code: str) -> List[TelegramAccount]:
    """Get accounts for a user filtered by country"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        return db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.country_code == country_code,
            TelegramAccount.is_active == True
        ).all()


def get_user_accounts_by_date(
    telegram_id: int,
    country_code: str = None,
    year: str = None,
    month: str = None,
    day: str = None
) -> List[TelegramAccount]:
    """Get accounts for a user filtered by date components"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        query = db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        )
        
        if country_code:
            query = query.filter(TelegramAccount.country_code == country_code)
        if year:
            query = query.filter(TelegramAccount.added_year == year)
        if month:
            query = query.filter(TelegramAccount.added_month == month)
        if day:
            query = query.filter(TelegramAccount.added_day == day)
        
        return query.all()


def get_user_countries(telegram_id: int) -> List[str]:
    """Get list of countries with accounts for a user (hides empty categories)"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        # Get distinct countries with active accounts
        results = db.query(TelegramAccount.country_code, TelegramAccount.country_name).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        ).distinct().all()
        
        return [(r.country_code, r.country_name) for r in results]


def get_user_dates_for_country(telegram_id: int, country_code: str) -> List[str]:
    """Get list of dates (YYYY/MM/DD) for a user's accounts in a country"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        # Get distinct dates with accounts
        results = db.query(
            TelegramAccount.added_year,
            TelegramAccount.added_month,
            TelegramAccount.added_day
        ).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.country_code == country_code,
            TelegramAccount.is_active == True
        ).distinct().all()
        
        return [f"{r.added_year}/{r.added_month}/{r.added_day}" for r in results]


def delete_account(telegram_id: int, account_id: int) -> bool:
    """Delete (deactivate) an account"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return False
        
        account = db.query(TelegramAccount).filter(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == user.id
        ).first()
        
        if account:
            account.is_active = False
            return True
        return False


# ============================================================================
# Statistics Operations
# ============================================================================

def get_user_stats(telegram_id: int) -> Dict[str, Any]:
    """Get statistics for a user"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return {}
        
        # Total accounts
        total_accounts = db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        ).count()
        
        # Accounts by country
        country_stats = db.query(
            TelegramAccount.country_code,
            TelegramAccount.country_name,
            func.count(TelegramAccount.id)
        ).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        ).group_by(TelegramAccount.country_code, TelegramAccount.country_name).all()
        
        # Accounts by date
        date_stats = db.query(
            TelegramAccount.added_date,
            func.count(TelegramAccount.id)
        ).filter(
            TelegramAccount.user_id == user.id,
            TelegramAccount.is_active == True
        ).group_by(TelegramAccount.added_date).all()
        
        return {
            'total_accounts': total_accounts,
            'by_country': {f"{c[0]} ({c[1]})": c[2] for c in country_stats},
            'by_date': {d[0]: d[1] for d in date_stats}
        }


# ============================================================================
# Proxy Operations
# ============================================================================

def add_proxy(
    telegram_id: int,
    host: str,
    port: int,
    username: str = None,
    password: str = None,
    name: str = None
) -> Proxy:
    """Add a proxy for a user"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            raise ValueError(f"User with telegram_id {telegram_id} not found")
        
        proxy = Proxy(
            user_id=user.id,
            host=host,
            port=port,
            username=username,
            password=password,
            name=name
        )
        
        db.add(proxy)
        db.flush()
        return proxy


def get_user_proxies(telegram_id: int) -> List[Proxy]:
    """Get all proxies for a user"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return []
        
        return db.query(Proxy).filter(
            Proxy.user_id == user.id,
            Proxy.is_active == True
        ).all()


def delete_proxy(telegram_id: int, proxy_id: int) -> bool:
    """Delete (deactivate) a proxy"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            return False
        
        proxy = db.query(Proxy).filter(
            Proxy.id == proxy_id,
            Proxy.user_id == user.id
        ).first()
        
        if proxy:
            proxy.is_active = False
            return True
        return False


# ============================================================================
# Whitelist Operations
# ============================================================================

def check_user_whitelisted(telegram_id: int) -> bool:
    """Check if a user is whitelisted"""
    with get_db() as db:
        # Check if user exists in whitelist table
        whitelist_entry = db.query(WhitelistEntry).filter(
            WhitelistEntry.telegram_id == str(telegram_id)
        ).first()
        
        if whitelist_entry:
            return True
        
        # Also check config file whitelist
        config = load_config()
        admin_ids = config.get('whitelist', {}).get('admin_ids', [])
        
        return str(telegram_id) in [str(uid) for uid in admin_ids]


def add_to_whitelist(telegram_id: int, username: str = None, added_by: str = None, notes: str = None):
    """Add a user to the whitelist"""
    with get_db() as db:
        existing = db.query(WhitelistEntry).filter(
            WhitelistEntry.telegram_id == str(telegram_id)
        ).first()
        
        if not existing:
            entry = WhitelistEntry(
                telegram_id=str(telegram_id),
                username=username,
                added_by=added_by,
                notes=notes
            )
            db.add(entry)


def remove_from_whitelist(telegram_id: int) -> bool:
    """Remove a user from the whitelist"""
    with get_db() as db:
        entry = db.query(WhitelistEntry).filter(
            WhitelistEntry.telegram_id == str(telegram_id)
        ).first()
        
        if entry:
            db.delete(entry)
            return True
        return False


def get_whitelist() -> List[WhitelistEntry]:
    """Get all whitelisted users"""
    with get_db() as db:
        return db.query(WhitelistEntry).all()


# func is imported at the top with other sqlalchemy imports
