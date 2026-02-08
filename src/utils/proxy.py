"""
Telegram Account Manager - Proxy Management Utilities

SOCKS5 proxy support for preventing Telegram account bans.
"""

import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx


@dataclass
class SOCKS5Proxy:
    """
    SOCKS5 proxy configuration.
    
    Attributes:
        host: Proxy server hostname or IP
        port: Proxy server port
        username: Authentication username (optional)
        password: Authentication password (optional)
        proxy_type: socks5, socks4, http
    """
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "socks5"
    
    @property
    def url(self) -> str:
        """Get the proxy URL for Telethon."""
        if self.username and self.password:
            return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"socks5://{self.host}:{self.port}"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if proxy requires authentication."""
        return bool(self.username and self.password)
    
    def validate(self) -> bool:
        """
        Validate proxy configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.host or not self.host.strip():
            return False
        
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            return False
        
        return True


class ProxyManager:
    """
    Manager for SOCKS5 proxies.
    
    Features:
    - Validate proxy connectivity
    - Test proxy authentication
    - Rotate proxies
    """
    
    def __init__(self):
        """Initialize the proxy manager."""
        self._proxies: dict[int, SOCKS5Proxy] = {}
    
    def add_proxy(self, user_id: int, proxy: SOCKS5Proxy) -> bool:
        """
        Add a proxy for a user.
        
        Args:
            user_id: Telegram user ID
            proxy: Proxy configuration
            
        Returns:
            True if added successfully
        """
        if not proxy.validate():
            return False
        
        self._proxies[user_id] = proxy
        return True
    
    def remove_proxy(self, user_id: int, proxy_id: int) -> bool:
        """
        Remove a proxy for a user.
        
        Args:
            user_id: Telegram user ID
            proxy_id: Proxy ID
            
        Returns:
            True if removed successfully
        """
        # TODO: Implement with database
        return False
    
    def get_proxy(self, user_id: int) -> Optional[SOCKS5Proxy]:
        """
        Get the active proxy for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Proxy configuration or None
        """
        return self._proxies.get(user_id)
    
    async def test_connection(
        self, 
        proxy: SOCKS5Proxy,
        timeout: float = 10.0
    ) -> tuple[bool, str]:
        """
        Test if a proxy connection works.
        
        Args:
            proxy: Proxy configuration
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (success, message)
        """
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                proxies={
                    "http": proxy.url,
                    "https": proxy.url,
                },
            ) as client:
                # Test connection to Telegram
                response = await client.get(
                    "https://api.telegram.org",
                    timeout=timeout,
                )
                
                if response.status_code == 200:
                    return True, "Proxy connection successful"
                else:
                    return False, f"Connection failed: HTTP {response.status_code}"
                    
        except httpx.TimeoutException:
            return False, "Connection timed out"
        except httpx.ConnectError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def test_authentication(
        self, 
        proxy: SOCKS5Proxy,
        timeout: float = 10.0
    ) -> tuple[bool, str]:
        """
        Test proxy authentication.
        
        Args:
            proxy: Proxy configuration
            timeout: Authentication timeout
            
        Returns:
            Tuple of (success, message)
        """
        if not proxy.is_authenticated:
            return True, "No authentication required"
        
        # Test authentication by connecting
        success, message = await self.test_connection(proxy, timeout)
        
        if success:
            return True, "Authentication successful"
        
        return False, f"Authentication failed: {message}"
    
    @staticmethod
    def parse_proxy_url(url: str) -> Optional[SOCKS5Proxy]:
        """
        Parse a proxy URL string.
        
        Args:
            url: Proxy URL (e.g., socks5://host:port or socks5://user:pass@host:port)
            
        Returns:
            SOCKS5Proxy object or None if invalid
        """
        try:
            parsed = urlparse(url)
            
            host = parsed.hostname
            port = parsed.port
            
            if not host or not port:
                return None
            
            # Determine proxy type
            proxy_type = parsed.scheme
            
            # Extract credentials
            username = parsed.username
            password = parsed.password
            
            return SOCKS5Proxy(
                host=host,
                port=port,
                username=username,
                password=password,
                proxy_type=proxy_type,
            )
            
        except Exception:
            return None
    
    @staticmethod
    def format_proxy_for_display(proxy: SOCKS5Proxy) -> str:
        """
        Format a proxy for display (masked credentials).
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Formatted string
        """
        if proxy.is_authenticated:
            return f"socks5://***:***@{proxy.host}:{proxy.port}"
        return f"socks5://{proxy.host}:{proxy.port}"


# Global proxy manager instance
proxy_manager = ProxyManager()


def validate_proxy_config(
    host: str,
    port: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Validate proxy configuration.
    
    Args:
        host: Proxy host
        port: Proxy port
        username: Username (optional)
        password: Password (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate host
    if not host or not host.strip():
        return False, "Host cannot be empty"
    
    # Validate port
    if not isinstance(port, int) or not (1 <= port <= 65535):
        return False, "Port must be between 1 and 65535"
    
    # Validate credentials
    if (username and not password) or (password and not username):
        return False, "Both username and password must be provided"
    
    return True, "Valid"
