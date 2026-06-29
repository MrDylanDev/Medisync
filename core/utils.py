import logging
import re
from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.text import slugify

logger = logging.getLogger(__name__)

LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCKOUT_MINUTES = 15


def _login_cache_key(email):
    return f'login_attempts:{email}'


def is_login_locked(email):
    """Return True if the account is currently locked out."""
    attempts = cache.get(_login_cache_key(email), 0)
    return attempts >= LOGIN_MAX_ATTEMPTS


def register_failed_attempt(email):
    """Increment failed attempt counter. Locks after MAX_ATTEMPTS."""
    key = _login_cache_key(email)
    attempts = cache.get(key, 0) + 1
    timeout = LOGIN_LOCKOUT_MINUTES * 60
    cache.set(key, attempts, timeout=timeout)
    return attempts


def reset_login_attempts(email):
    """Clear failed attempt counter on successful login."""
    cache.delete(_login_cache_key(email))


def validate_cuit(cuit: str) -> bool:
    """
    Validate an Argentine CUIT (Clave Única de Identificación Tributaria).
    
    CUIT format: XX-XXXXXXXX-X or XXXXXXXXXXX
    Uses the AFIP validation algorithm (module 11).
    
    Args:
        cuit: The CUIT string to validate (with or without hyphens).
    
    Returns:
        True if the CUIT is valid, False otherwise.
    """
    # Remove hyphens and whitespace
    cuit = re.sub(r'[\s-]', '', cuit)
    
    # Must be exactly 11 digits
    if not cuit.isdigit() or len(cuit) != 11:
        return False
    
    # Validate check digit using module 11 algorithm
    multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(cuit[i]) * multipliers[i] for i in range(10))
    remainder = total % 11
    check_digit = 11 - remainder
    
    if check_digit == 11:
        check_digit = 0
    elif check_digit == 10:
        check_digit = 9
    
    return check_digit == int(cuit[10])


def format_cuit(cuit: str) -> str:
    """
    Format a CUIT string with hyphens: XX-XXXXXXXX-X.
    
    Args:
        cuit: Raw CUIT string (11 digits).
    
    Returns:
        Formatted CUIT or the original string if invalid.
    """
    digits = re.sub(r'[\s-]', '', cuit)
    if len(digits) == 11 and digits.isdigit():
        return f'{digits[:2]}-{digits[2:10]}-{digits[10:]}'
    return cuit


def date_range(start_date: date, end_date: date):
    """
    Generate a range of dates from start_date to end_date (inclusive).
    
    Args:
        start_date: The start date.
        end_date: The end date (must be >= start_date).
    
    Yields:
        Each date in the range.
    """
    if end_date < start_date:
        raise ValueError('end_date must be >= start_date')
    
    current = start_date
    while current <= end_date:
        yield current
        from datetime import timedelta
        current += timedelta(days=1)


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: The text to slugify.
        max_length: Maximum length of the slug (default: 50).
    
    Returns:
        A clean slug string.
    """
    slug = slugify(text)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    return slug


def parse_argentine_date(date_str: str) -> date:
    """
    Parse an Argentine-formatted date string (DD/MM/YYYY).
    
    Args:
        date_str: Date string in DD/MM/YYYY format.
    
    Returns:
        A date object.
    
    Raises:
        ValueError: If the string cannot be parsed.
    """
    return datetime.strptime(date_str, '%d/%m/%Y').date()


def send_template_email(subject, template_name, context, recipient_list):
    """
    Send an email by rendering a Django template to HTML.

    Args:
        subject: Email subject line.
        template_name: Path to the template (e.g. 'emails/registration_confirm.html').
        context: Template context dictionary. site_name, protocol, and domain
                 are auto-injected from settings.
        recipient_list: List of email addresses.

    Returns:
        The number of successfully delivered messages.
    """
    context.setdefault('site_name', 'Medisync')
    context.setdefault('protocol', 'http')
    context.setdefault('domain', 'localhost:8000')

    html_message = render_to_string(template_name, context)
    plain_message = re.sub(r'<[^>]+>', '', html_message)

    sent = send_mail(
        subject=subject,
        message=plain_message.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )
    return sent
