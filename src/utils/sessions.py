# Telegram Account Management Bot - Session Export Utility
# Handle exporting Telegram sessions for Telethon and Pyrogram

import os
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, BinaryIO
from datetime import datetime

# Session file extensions
TELETHON_EXT = '.session'
PYROGRAM_EXT = '.session'


def get_sessions_dir() -> Path:
    """Get the sessions directory path"""
    return Path(__file__).parent.parent.parent / 'data' / 'sessions'


def get_exports_dir() -> Path:
    """Get the exports directory path"""
    return Path(__file__).parent.parent.parent / 'data' / 'exports'


def export_telethon_format(session_files: List[Path], output_dir: Path) -> List[Path]:
    """
    Export session files in Telethon format.
    
    Telethon uses a single .session file containing all session data.
    
    Args:
        session_files: List of session file paths
        output_dir: Output directory for exported files
        
    Returns:
        List of exported file paths
    """
    exported_files = []
    
    for session_file in session_files:
        if session_file.exists():
            dest = output_dir / f"{session_file.stem}{TELETHON_EXT}"
            shutil.copy2(session_file, dest)
            exported_files.append(dest)
    
    return exported_files


def export_pyrogram_format(session_files: List[Path], output_dir: Path) -> List[Path]:
    """
    Export session files in Pyrogram format.
    
    Pyrogram uses a single .session file containing all session data.
    
    Args:
        session_files: List of session file paths
        output_dir: Output directory for exported files
        
    Returns:
        List of exported file paths
    """
    exported_files = []
    
    for session_file in session_files:
        if session_file.exists():
            dest = output_dir / f"{session_file.stem}{PYROGRAM_EXT}"
            shutil.copy2(session_file, dest)
            exported_files.append(dest)
    
    return exported_files


def export_sessions(
    session_files: List[Path],
    format: str = 'telethon',
    count: Optional[int] = None
) -> Path:
    """
    Export session files in the specified format.
    
    Args:
        session_files: List of session file paths to export
        format: Export format ('telethon' or 'pyrogram')
        count: Maximum number of sessions to export (None for all)
        
    Returns:
        Path to the exported file or directory
    """
    # Limit count if specified
    if count and count > 0:
        session_files = session_files[:count]
    
    exports_dir = get_exports_dir()
    exports_dir.mkdir(exist_ok=True)
    
    # Create a timestamped subdirectory for this export
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = exports_dir / f"export_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    # Export in the specified format
    if format.lower() == 'telethon':
        exported = export_telethon_format(session_files, output_dir)
    elif format.lower() == 'pyrogram':
        exported = export_pyrogram_format(session_files, output_dir)
    else:
        raise ValueError(f"Unknown export format: {format}")
    
    return output_dir, exported


def export_sessions_zip(
    session_files: List[Path],
    format: str = 'telethon',
    count: Optional[int] = None,
    include_stats: bool = False
) -> Path:
    """
    Export session files as a ZIP archive.
    
    Args:
        session_files: List of session file paths to export
        format: Export format ('telethon' or 'pyrogram')
        count: Maximum number of sessions to export (None for all)
        include_stats: Include statistics file in the archive
        
    Returns:
        Path to the ZIP file
    """
    # Limit count if specified
    if count and count > 0:
        session_files = session_files[:count]
    
    exports_dir = get_exports_dir()
    exports_dir.mkdir(exist_ok=True)
    
    # Create a temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Export sessions
        output_dir, exported = export_sessions(session_files, format, count, temp_path)
        
        # Include statistics if requested
        if include_stats:
            stats_file = output_dir / 'stats.txt'
            with open(stats_file, 'w') as f:
                f.write(f"Export Date: {datetime.now().isoformat()}\n")
                f.write(f"Format: {format}\n")
                f.write(f"Total Sessions: {len(exported)}\n")
                f.write(f"\nSession Files:\n")
                for i, file in enumerate(exported, 1):
                    f.write(f"  {i}. {file.name}\n")
        
        # Create ZIP file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f"telegram_accounts_{format}_{timestamp}.zip"
        zip_path = exports_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.name
                    zipf.write(file_path, arcname)
        
        return zip_path


def get_user_sessions(user_id: int) -> List[Path]:
    """
    Get all session files for a specific user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        List of session file paths
    """
    sessions_dir = get_sessions_dir()
    sessions_dir.mkdir(exist_ok=True)
    
    # Find session files for this user
    user_prefix = f"user_{user_id}_"
    session_files = []
    
    for file in sessions_dir.glob('*'):
        if file.is_file() and file.name.startswith(user_prefix):
            session_files.append(file)
    
    return sorted(session_files)


def delete_session(session_file: Path) -> bool:
    """
    Delete a session file.
    
    Args:
        session_file: Path to the session file
        
    Returns:
        True if deleted successfully
    """
    try:
        if session_file.exists():
            session_file.unlink()
            # Also delete associated files (.session-journal, etc.)
            for ext in ['-journal', '.sqlite', '.sqlite3']:
                alt_file = session_file.with_suffix(session_file.suffix + ext)
                if alt_file.exists():
                    alt_file.unlink()
        return True
    except Exception:
        return False


def get_session_info(session_file: Path) -> dict:
    """
    Get information about a session file.
    
    Args:
        session_file: Path to the session file
        
    Returns:
        Dictionary with session information
    """
    info = {
        'name': session_file.name,
        'size': session_file.stat().st_size if session_file.exists() else 0,
        'modified': datetime.fromtimestamp(session_file.stat().st_mtime).isoformat() if session_file.exists() else None,
        'exists': session_file.exists()
    }
    
    return info


if __name__ == '__main__':
    # Test export functionality
    print("Testing session export utilities...")
    
    # Create test sessions
    with tempfile.TemporaryDirectory() as temp_dir:
        sessions_dir = Path(temp_dir) / 'sessions'
        sessions_dir.mkdir()
        
        # Create dummy session files
        for i in range(3):
            test_file = sessions_dir / f"test_session_{i}.session"
            with open(test_file, 'w') as f:
                f.write(f"Test session {i} content")
        
        # Test export
        session_files = list(sessions_dir.glob('*.session'))
        print(f"Created {len(session_files)} test sessions")
        
        zip_path = export_sessions_zip(session_files, 'telethon', count=2)
        print(f"Exported to: {zip_path}")
        
        if zip_path.exists():
            print(f"ZIP file size: {zip_path.stat().st_size} bytes")
