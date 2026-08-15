import re
from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_url(target):
    """Validates that target URL is a safe local redirect URL.
    
    Prevents open redirect vulnerabilities by rejecting:
    - Protocol-relative URLs (e.g. //evil.com or \\evil.com)
    - External domains (e.g. http://evil.com)
    """
    if not target or not isinstance(target, str):
        return False

    target_str = target.strip()
    if target_str.startswith('//') or target_str.startswith('\\'):
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target_str))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def validate_password_strength(password):
    """Validates password strength against security requirements.
    
    Requirements:
    - Minimum 8 characters, maximum 128 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []
    if not password:
        return False, ["Password is required."]

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if len(password) > 128:
        errors.append("Password must not exceed 128 characters.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit.")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        errors.append("Password must contain at least one special character (e.g. !@#$%^&*).")

    return len(errors) == 0, errors
