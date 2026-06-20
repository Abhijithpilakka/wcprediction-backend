from supabase import create_client, Client
from functools import lru_cache
from fastapi import HTTPException
import httpx
import httpcore
from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    # pydantic's AnyUrl yields a Url object; convert to str for supabase client
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)


def safe_execute(request_builder):
    """Execute a PostgREST request builder and map network/errors to HTTP 502.

    Pass the request builder returned by `sb.table(...).select(...)` etc.
    """
    try:
        return request_builder.execute()
    except (httpx.ConnectError, httpcore.ConnectError) as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to Supabase: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase request failed: {e}") from e
