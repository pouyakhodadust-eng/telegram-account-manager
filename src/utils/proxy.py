# Telegram Account Management Bot - SOCKS5 Proxy Utility
# Handle proxy validation and configuration

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

# SOCKS5 proxy regex patterns
SOCKS5_PATTERN = re.compile(
    r'^(?:(?P<scheme>socks5)://)?'
    r'(?:(?P<user>[^:]+):(?P<pass>[^@]+)@)?'
    r'(?P<host>[^:]+):(?P<port>\d+)$',
    re.IGNORECASE
)


def validate_proxy(host: str, port: int, username: Optional[str] = None, password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate SOCKS5 proxy configuration.
    
    Args:
        host: Proxy host (IP or domain)
        port: Proxy port
        username: Optional username for authentication
        password: Optional password for authentication
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate host
    if not host or len(host) < 1:
        return False, "Host cannot be empty"
    
    if len(host) > 255:
        return False, "Host name is too long"
    
    # Check for valid IP or domain
    ip_pattern = re.compile(
        r'^(\d{1,3}\.){3}\d{1,3}$'
    )
    domain_pattern = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    )
    
    if not (ip_pattern.match(host) or domain_pattern.match(host)):
        return False, "Invalid host format"
    
    # Validate port
    if not (1 <= port <= 65535):
        return False, "Port must be between 1 and 65535"
    
    # Validate credentials if provided
    if username:
        if len(username) > 255:
            return False, "Username is too long"
        if ':' in username:
            return False, "Username cannot contain colons"
    
    if password:
        if len(password) > 255:
            return False, "Password is too long"
    
    return True, ""


def parse_proxy_string(proxy_string: str) -> Optional[dict]:
    """
    Parse a proxy string in various formats.
    
    Supported formats:
    - host:port
    - host:port:username:password
    - socks5://host:port
    - socks5://username:password@host:port
    
    Args:
        proxy_string: Proxy configuration string
        
    Returns:
        Dictionary with proxy configuration or None if invalid
    """
    if not proxy_string:
        return None
    
    # Try SOCKS5 pattern first
    match = SOCKS5_PATTERN.match(proxy_string.strip())
    
    if match:
        groups = match.groupdict()
        return {
            'scheme': groups.get('scheme', 'socks5'),
            'host': groups['host'],
            'port': int(groups['port']),
            'username': groups.get('user'),
            'password': groups.get('pass')
        }
    
    # Try URL format
    if '://' in proxy_string:
        try:
            parsed = urlparse(proxy_string)
            
            if parsed.scheme in ['socks5', 'socks5h']:
                return {
                    'scheme': 'socks5',
                    'host': parsed.hostname,
                    'port': parsed.port,
                    'username': parsed.username,
                    'password': parsed.password
                }
        except Exception:
            pass
    
    # Try simple host:port format
    try:
        host, port = proxy_string.rsplit(':', 1)
        return {
            'scheme': 'socks5',
            'host': host.strip(),
            'port': int(port.strip()),
            'username': None,
            'password': None
        }
    except (ValueError, AttributeError):
        pass
    
    return None


def create_proxy_url(host: str, port: int, username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Create a SOCKS5 proxy URL.
    
    Args:
        host: Proxy host
        port: Proxy port
        username: Optional username
        password: Optional password
        
    Returns:
        Proxy URL string
    """
    if username and password:
        return f"socks5://{username}:{password}@{host}:{port}"
    else:
        return f"socks5://{host}:{port}"


def parse_telethon_proxy(proxy_dict: dict) -> dict:
    """
    Parse proxy configuration for Telethon.
    
    Telethon expects: (proxy_type, proxy_addr, port, rdns, username, password)
    
    Args:
        proxy_dict: Proxy configuration dictionary
        
    Returns:
        Telethon-compatible proxy tuple
    """
    return (
        'socks5',  # proxy type
        proxy_dict.get('host', ''),
        proxy_dict.get('port', 1080),
        True,  # rdns
        proxy_dict.get('username'),
        proxy_dict.get('password')
    )


def parse_pyrogram_proxy(proxy_dict: dict) -> dict:
    """
    Parse proxy configuration for Pyrogram.
    
    Pyrogram expects: {"scheme": "socks5", "hostname": "...", "port": ..., ...}
    
    Args:
        proxy_dict: Proxy configuration dictionary
        
    Returns:
        Pyrogram-compatible proxy dictionary
    """
    return {
        'scheme': 'socks5',
        'hostname': proxy_dict.get('host', ''),
        'port': proxy_dict.get('port', 1080),
        'username': proxy_dict.get('username'),
        'password': proxy_dict.get('password')
    }


def test_proxy_connection(proxy_dict: dict, timeout: float = 5.0) -> Tuple[bool, str]:
    """
    Test if a proxy is reachable.
    
    Args:
        proxy_dict: Proxy configuration dictionary
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (is_reachable, message)
    """
    import socket
    
    host = proxy_dict.get('host')
    port = proxy_dict.get('port', 1080)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True, f"Proxy {host}:{port} is reachable"
    except socket.error as e:
        return False, f"Failed to connect to proxy: {e}"


if __name__ == '__main__':
    # Test the module
    test_cases = [
        "192.168.1.1:1080",
        "proxy.example.com:1080",
        "user:pass@192.168.1.1:1080",
        "socks5://proxy.example.com:1080",
        "socks5://user:pass@proxy.example.com:1080",
    ]
    
    for test in test_cases:
        result = parse_proxy_string(test)
        print(f"\nInput: {test}")
        print(f"Parsed: {result}")
        
        if result:
            valid, msg = validate_proxy(
                result['host'],
                result['port'],
                result.get('username'),
                result.get('password')
            )
            print(f"Valid: {valid} - {msg}")
