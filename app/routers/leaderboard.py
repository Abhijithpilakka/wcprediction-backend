from fastapi import APIRouter, Depends, Query
from app.core.supabase import get_supabase, safe_execute
from app.core.auth import get_current_user
from app.services.leaderboard import get_current_week

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/overall")
def overall_leaderboard(
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase()
    result = safe_execute(
        sb.table("overall_leaderboard")
        .select("rank, points, exact_scores, users(id, name, phone_number)")
        .order("rank")
        .limit(limit)
    )
    # Also return caller's rank
    my_rank = safe_execute(
        sb.table("overall_leaderboard")
        .select("rank, points")
        .eq("user_id", current_user["id"])
        .single()
    )
    return {
        "leaderboard": result.data,
        "my_rank": my_rank.data,
    }


@router.get("/weekly")
def weekly_leaderboard(
    week: int = Query(default=None),
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase()
    week_num = week or get_current_week()

    result = safe_execute(
        sb.table("weekly_leaderboard")
        .select("rank, points, users(id, name, phone_number)")
        .eq("week_number", week_num)
        .order("rank")
        .limit(limit)
    )
    my_rank = safe_execute(
        sb.table("weekly_leaderboard")
        .select("rank, points")
        .eq("user_id", current_user["id"])
        .eq("week_number", week_num)
        .single()
    )
    return {
        "week": week_num,
        "leaderboard": result.data,
        "my_rank": my_rank.data,
    }
