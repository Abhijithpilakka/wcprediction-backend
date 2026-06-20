from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.schemas.schemas import MatchCreate, MatchUpdate, ResultUpdate, BanUserRequest
from app.core.supabase import get_supabase, safe_execute
from app.core.auth import require_admin
from app.services.points import calc_points
from app.services.leaderboard import recompute_all

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── Match Management ─────────────────────────────────────────────────────────

@router.post("/matches")
def add_match(body: MatchCreate, admin=Depends(require_admin)):
    sb = get_supabase()
    result = safe_execute(sb.table("matches").insert({
        "team1": body.team1,
        "team2": body.team2,
        "kickoff_time": body.kickoff_time.isoformat(),
        "stage": body.stage,
        "status": "upcoming",
        "multiplier": body.multiplier,
        "actual_team1_score": None,
        "actual_team2_score": None,
    }))
    return result.data[0]


@router.patch("/matches/{match_id}")
def update_match(match_id: str, body: MatchUpdate, admin=Depends(require_admin)):
    sb = get_supabase()
    updates = body.model_dump(exclude_none=True)
    if "kickoff_time" in updates:
        updates["kickoff_time"] = updates["kickoff_time"].isoformat()
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = safe_execute(sb.table("matches").update(updates).eq("id", match_id))
    return result.data[0]


@router.delete("/matches/{match_id}")
def delete_match(match_id: str, admin=Depends(require_admin)):
    sb = get_supabase()
    safe_execute(sb.table("predictions").delete().eq("match_id", match_id))
    safe_execute(sb.table("matches").delete().eq("id", match_id))
    return {"success": True}


# ─── Result Entry ─────────────────────────────────────────────────────────────

@router.post("/matches/{match_id}/result")
def enter_result(
    match_id: str,
    body: ResultUpdate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """
    Enter the final score for a match.
    Triggers automatic point calculation for all predictions on this match.
    Leaderboard recompute runs in the background.
    """
    sb = get_supabase()

    # 1. Update match
    safe_execute(sb.table("matches").update({
        "actual_team1_score": body.team1_score,
        "actual_team2_score": body.team2_score,
        "status": "completed",
    }).eq("id", match_id))

    # 2. Fetch match multiplier
    match_result = safe_execute(sb.table("matches").select("multiplier").eq("id", match_id).single())
    multiplier = match_result.data["multiplier"]

    # 3. Fetch all predictions for this match
    preds = safe_execute(sb.table("predictions").select("*").eq("match_id", match_id)).data

    # 4. Calculate and update points
    for pred in preds:
        pts = calc_points(
            pred["predicted_team1_score"],
            pred["predicted_team2_score"],
            body.team1_score,
            body.team2_score,
            multiplier,
        )
        is_exact = (
            pred["predicted_team1_score"] == body.team1_score
            and pred["predicted_team2_score"] == body.team2_score
        )

        # Update prediction row
        safe_execute(sb.table("predictions").update({
            "points_awarded": pts,
            "is_locked": True,
        }).eq("id", pred["id"]))

        # Update user totals
        user = safe_execute(sb.table("users").select("total_points, weekly_points, exact_predictions").eq("id", pred["user_id"]).single()).data
        safe_execute(sb.table("users").update({
            "total_points": user["total_points"] + pts,
            "weekly_points": user["weekly_points"] + pts,
            "exact_predictions": user["exact_predictions"] + (1 if is_exact else 0),
        }).eq("id", pred["user_id"]))

    # 5. Recompute leaderboards in background
    background_tasks.add_task(recompute_all)

    return {"success": True, "predictions_scored": len(preds)}


@router.post("/matches/{match_id}/go-live")
def set_match_live(match_id: str, admin=Depends(require_admin)):
    """Mark a match as live and lock all its predictions."""
    sb = get_supabase()
    safe_execute(sb.table("matches").update({"status": "live"}).eq("id", match_id))
    safe_execute(sb.table("predictions").update({"is_locked": True}).eq("match_id", match_id))
    return {"success": True}


# ─── User Management ─────────────────────────────────────────────────────────

@router.get("/users")
def list_users(admin=Depends(require_admin)):
    sb = get_supabase()
    result = safe_execute(sb.table("users").select("*").order("total_points", desc=True))
    return result.data


@router.patch("/users/ban")
def ban_user(body: BanUserRequest, admin=Depends(require_admin)):
    sb = get_supabase()
    result = safe_execute(sb.table("users").update({"is_banned": body.banned}).eq("id", body.user_id))
    return result.data[0]


@router.patch("/users/{user_id}/make-admin")
def make_admin(user_id: str, admin=Depends(require_admin)):
    sb = get_supabase()
    result = safe_execute(sb.table("users").update({"is_admin": True}).eq("id", user_id))
    return result.data[0]


# ─── Leaderboard ─────────────────────────────────────────────────────────────

@router.post("/recompute")
def recompute(background_tasks: BackgroundTasks, admin=Depends(require_admin)):
    """Manually trigger a full leaderboard recompute."""
    background_tasks.add_task(recompute_all)
    return {"success": True, "message": "Leaderboard recompute triggered"}


@router.post("/reset-weekly")
def reset_weekly(admin=Depends(require_admin)):
    """Reset weekly points for all users (run at start of each week)."""
    sb = get_supabase()
    safe_execute(sb.table("users").update({"weekly_points": 0}).neq("id", "00000000-0000-0000-0000-000000000000"))
    recompute_all()
    return {"success": True}
