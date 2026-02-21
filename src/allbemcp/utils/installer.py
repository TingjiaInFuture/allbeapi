# -*- coding: utf-8 -*-
import sys
import subprocess
import importlib.util
import logging
import re

# Configure basic logging: Pure English, no rich text
# logging.basicConfig(level=logging.INFO, format='[AutoInstall] %(message)s')
logger = logging.getLogger(__name__)

# Mapping dictionary: "Import Name" -> "Pip Package Name"
# If a name is not in this dictionary, it assumes Import Name == Package Name.
PKG_MAPPING = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "bs4": "beautifulsoup4",
    "usb": "pyusb",
    "OpenSSL": "pyopenssl",
    "dateutil": "python-dateutil",
    "docx": "python-docx",
    "dotenv": "python-dotenv",
    "dns": "dnspython",
    "serial": "pyserial",
    "mysqldb": "mysqlclient",
    "wx": "wxPython",
    "git": "GitPython",
    "telegram": "python-telegram-bot",
    "google.protobuf": "protobuf",
    "crypto": "pycryptodome"
}

def _get_pip_name(import_name: str) -> str:
    """
    Resolves the pip package name from the import name.
    """
    # Handle sub-modules (e.g., 'sklearn.metrics' -> 'sklearn')
    root_package = import_name.split('.')[0]
    return PKG_MAPPING.get(root_package, root_package)

def _is_installed(import_name: str) -> bool:
    """
    Checks if a library is installed using find_spec without importing it.
    """
    try:
        spec = importlib.util.find_spec(import_name)
        return spec is not None
    except (ImportError, AttributeError, ValueError):
        return False


def is_dependency_installed(import_name: str) -> bool:
    """Public helper to check whether dependency can be imported."""
    return _is_installed(import_name)

def install_dependency(import_name: str, auto_confirm: bool = True):
    """
    Checks for the existence of a library and installs it via pip if missing.
    
    Args:
        import_name (str): The name used in the import statement (e.g., 'cv2', 'requests').
    """
    # 1. Check if already installed
    if _is_installed(import_name):
        return

    # 2. Resolve the actual package name for pip
    target_package = _get_pip_name(import_name)
    
    # Security check: Ensure package name is valid to prevent injection
    if not re.match(r'^[a-zA-Z0-9_\-]+$', target_package):
        logger.error(f"Invalid package name: '{target_package}'. Installation aborted.")
        raise ValueError(f"Invalid package name: {target_package}")

    if not auto_confirm:
        try:
            response = input(f"Install missing dependency '{target_package}' for import '{import_name}'? [y/N]: ").strip().lower()
        except EOFError:
            response = ""
        if response not in ("y", "yes"):
            raise RuntimeError(f"User declined installation for package '{target_package}'")
    
    print(f"[INSTALL] Missing dependency: '{import_name}'. Installing package: '{target_package}'...")
    logger.info(f"Missing dependency: '{import_name}'. Installing package: '{target_package}'...")

    # 3. Build command: Ensure pip runs for the current Python interpreter
    install_cmd = [sys.executable, "-m", "pip", "install", target_package]

    try:
        # check_call blocks until completion and raises CalledProcessError on failure
        subprocess.check_call(install_cmd)
        
        # 4. Critical: Invalidate caches so the new library can be imported immediately
        importlib.invalidate_caches()
        
        print(f"[INSTALL] Successfully installed '{target_package}'.")
        logger.info(f"Successfully installed '{target_package}'.")
        
    except subprocess.CalledProcessError:
        logger.warning(f"Failed to install '{target_package}' globally. Trying user install...")
        print(f"[INSTALL] Global install failed. Trying user install for '{target_package}'...")
        try:
            # Try installing with --user
            install_cmd.append("--user")
            subprocess.check_call(install_cmd)
            importlib.invalidate_caches()
            print(f"[INSTALL] Successfully installed '{target_package}' (user mode).")
            logger.info(f"Successfully installed '{target_package}' (user mode).")
        except subprocess.CalledProcessError:
            print(f"[INSTALL] Failed to install '{target_package}'. Please check network connection or permissions.")
            logger.error(f"Failed to install '{target_package}'. Please check network connection or permissions.")
            raise