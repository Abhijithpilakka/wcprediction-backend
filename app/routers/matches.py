from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase import get_supabase, safe_execute
from app.core.auth import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("")
def get_all_matches(current_user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = safe_execute(sb.table("matches").select("*").order("kickoff_time"))
    return result.data


@router.get("/upcoming")
def get_upcoming(current_user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = safe_execute(sb.table("matches").select("*").eq("status", "upcoming").order("kickoff_time"))
    return result.data


@router.get("/live")
def get_live(current_user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = safe_execute(sb.table("matches").select("*").eq("status", "live"))
    return result.data


@router.get("/completed")
def get_completed(current_user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = safe_execute(
        sb.table("matches")
        .select("*")
        .eq("status", "completed")
        .order("kickoff_time", desc=True)
    )
    return result.data


@router.get("/{match_id}")
def get_match(match_id: str, current_user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = safe_execute(sb.table("matches").select("*").eq("id", match_id).single())
    if not result.data:
        raise HTTPException(status_code=404, detail="Match not found")
    return result.data
