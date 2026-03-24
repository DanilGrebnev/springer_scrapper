"""Compatibility patches for third-party packages broken on modern Python."""
import sys

# ---------------------------------------------------------------------------
# aioredis: duplicate base class TimeoutError on Python 3.11+
# ---------------------------------------------------------------------------
if sys.version_info >= (3, 11):
    import asyncio
    import builtins

    _saved = asyncio.TimeoutError
    asyncio.TimeoutError = type("TimeoutError", (builtins.TimeoutError,), {})
    try:
        import aioredis  # noqa: F401
    finally:
        asyncio.TimeoutError = _saved
    del _saved

# ---------------------------------------------------------------------------
# bcrypt >=4.1 + passlib: removed __about__, strict 72-byte limit
# passlib's detect_wrap_bug() sends >72-byte test passwords which now raise.
# ---------------------------------------------------------------------------
try:
    import bcrypt as _bcrypt

    if not hasattr(_bcrypt, "__about__"):

        class _About:
            __version__ = getattr(_bcrypt, "__version__", "4.1.0")

        _bcrypt.__about__ = _About  # type: ignore[attr-defined]

    _orig_hashpw = _bcrypt.hashpw

    def _hashpw_compat(password: bytes, salt: bytes) -> bytes:
        if isinstance(password, bytes) and len(password) > 72:
            password = password[:72]
        return _orig_hashpw(password, salt)

    _bcrypt.hashpw = _hashpw_compat  # type: ignore[assignment]

    _orig_checkpw = _bcrypt.checkpw

    def _checkpw_compat(password: bytes, hashed_password: bytes) -> bool:
        if isinstance(password, bytes) and len(password) > 72:
            password = password[:72]
        return _orig_checkpw(password, hashed_password)

    _bcrypt.checkpw = _checkpw_compat  # type: ignore[assignment]
except ImportError:
    pass
