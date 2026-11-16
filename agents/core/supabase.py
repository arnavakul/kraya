
from supabase import Client, create_client

from core.config import settings


def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SECRET_KEY.get_secret_value(),
    )


supabase = get_supabase_client()
