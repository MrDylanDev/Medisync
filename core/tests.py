"""
Tests for core app: utils, middleware, context_processors.
"""
import pytest
from datetime import date, timedelta
from core.utils import (
    validate_cuit,
    format_cuit,
    date_range,
    generate_slug,
    parse_argentine_date,
)
from core.middleware import get_current_user, RequestUserMiddleware
from django.http import HttpRequest
from django.test import RequestFactory


# ─── Utils: validate_cuit ────────────────────────────────────────────────────

class TestValidateCuit:
    """Tests for CUIT validation function."""

    def test_valid_cuit_with_hyphens(self):
        """Valid CUIT with hyphens should return True."""
        # CUIT 20-12345678-6: computed with AFIP module 11 algorithm
        assert validate_cuit('20-12345678-6') is True

    def test_valid_cuit_without_hyphens(self):
        """Valid CUIT without hyphens should return True."""
        # Using a CUIT type 27 (female) with correct check digit
        assert validate_cuit('27000000006') is True

    def test_valid_cuit_formatted_when_unformatted(self):
        """CUIT without hyphens passes validation (checksum verified)."""
        assert validate_cuit('20123456786') is True

    def test_invalid_cuit_wrong_length(self):
        """CUIT with wrong length should return False."""
        assert validate_cuit('12345') is False
        assert validate_cuit('201234567890') is False

    def test_invalid_cuit_with_letters(self):
        """CUIT containing non-digits should return False."""
        assert validate_cuit('20-ABCD-5678-9') is False

    def test_invalid_cuit_check_digit(self):
        """CUIT with wrong check digit should return False."""
        assert validate_cuit('20-12345678-1') is False

    def test_empty_cuit(self):
        """Empty string should return False."""
        assert validate_cuit('') is False


# ─── Utils: format_cuit ──────────────────────────────────────────────────────

class TestFormatCuit:
    """Tests for CUIT formatting function."""

    def test_format_valid_cuit(self):
        """Valid 11-digit CUIT should be formatted with hyphens."""
        assert format_cuit('20123456789') == '20-12345678-9'

    def test_format_cuit_with_hyphens(self):
        """Already formatted CUIT should remain formatted."""
        assert format_cuit('20-12345678-9') == '20-12345678-9'

    def test_format_invalid_cuit(self):
        """Invalid CUIT should be returned as-is."""
        assert format_cuit('abc') == 'abc'


# ─── Utils: date_range ───────────────────────────────────────────────────────

class TestDateRange:
    """Tests for date_range generator."""

    def test_single_day_range(self):
        """Range with same start and end should yield one day."""
        d = date(2024, 1, 1)
        result = list(date_range(d, d))
        assert result == [d]

    def test_multi_day_range(self):
        """Range spanning multiple days should yield all days inclusive."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)
        result = list(date_range(start, end))
        assert result == [
            date(2024, 1, 1),
            date(2024, 1, 2),
            date(2024, 1, 3),
        ]

    def test_end_before_start_raises(self):
        """Range with end before start should raise ValueError."""
        with pytest.raises(ValueError, match='end_date must be >= start_date'):
            list(date_range(date(2024, 1, 10), date(2024, 1, 5)))

    def test_large_range_count(self):
        """Range over 30 days should yield exactly 31 days (inclusive)."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = list(date_range(start, end))
        assert len(result) == 31


# ─── Utils: generate_slug ────────────────────────────────────────────────────

class TestGenerateSlug:
    """Tests for slug generation."""

    def test_simple_text(self):
        """Simple text should produce a clean slug."""
        assert generate_slug('Hello World') == 'hello-world'

    def test_special_characters(self):
        """Special characters should be stripped."""
        assert generate_slug('¿Cómo estás?') == 'como-estas'

    def test_max_length_truncation(self):
        """Long text should be truncated to max_length."""
        long_text = 'a ' * 50
        slug = generate_slug(long_text, max_length=20)
        assert len(slug) <= 20

    def test_empty_text(self):
        """Empty text should produce empty slug."""
        assert generate_slug('') == ''


# ─── Utils: parse_argentine_date ─────────────────────────────────────────────

class TestParseArgentineDate:
    """Tests for Argentine date parsing."""

    def test_valid_date(self):
        """Valid DD/MM/YYYY should parse correctly."""
        result = parse_argentine_date('25/12/2024')
        assert result == date(2024, 12, 25)

    def test_invalid_format_raises(self):
        """Invalid format should raise ValueError."""
        with pytest.raises(ValueError):
            parse_argentine_date('2024-12-25')


# ─── Middleware ───────────────────────────────────────────────────────────────

class TestRequestUserMiddleware:
    """Tests for request user middleware."""

    def test_middleware_sets_user_on_request(self):
        """Middleware should store the request user in thread-local."""
        request = HttpRequest()
        request.user = 'test-user'
        factory = RequestFactory()

        def get_response(req):
            assert get_current_user() == 'test-user'
            from django.http import HttpResponse
            return HttpResponse('ok')

        middleware = RequestUserMiddleware(get_response)
        response = middleware(request)
        assert response.status_code == 200

    def test_middleware_no_user(self):
        """Middleware should handle request without user attribute."""
        request = HttpRequest()
        # No request.user set

        def get_response(req):
            assert get_current_user() is None
            from django.http import HttpResponse
            return HttpResponse('ok')

        middleware = RequestUserMiddleware(get_response)
        response = middleware(request)
        assert response.status_code == 200
