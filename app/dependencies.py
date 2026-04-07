# Re-export the two core dependencies so routers can import from one place
from app.auth.middleware import get_current_user, get_current_vault_user_id
from app.database import get_db

__all__ = ["get_db", "get_current_user", "get_current_vault_user_id"]
