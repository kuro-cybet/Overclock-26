import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """
    Returns the standard Supabase client (using anon key).
    Returns None if SUPABASE_URL or SUPABASE_KEY is not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase URL or Key not set. Supabase client is uninitialized.")
        return None

    try:
        clean_url = settings.SUPABASE_URL.rstrip("/").removesuffix("/rest/v1")
        _supabase_client = create_client(clean_url, settings.SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns the admin Supabase client (using service role key).
    Bypasses Row-Level Security for administrative operations.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    if not settings.SUPABASE_URL or not key:
        logger.warning("Supabase URL or Service Role Key not set.")
        return None

    try:
        clean_url = settings.SUPABASE_URL.rstrip("/").removesuffix("/rest/v1")
        _supabase_admin_client = create_client(clean_url, key)
        return _supabase_admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        return None

