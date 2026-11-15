from services.database import test_database_connection

def test_supabase_connection():
    assert test_database_connection() is True
    