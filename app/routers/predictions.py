from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import PredictionCreate
from app.core.supabase import get_supabase, safe_execute
from app.core.auth import get_current_user

router = APIRouter(prefix="/predictions", tags=["predictions"])

LOCK_MINUTES_BEFORE = 5


def _check_lock(match: dict):
    """Raise 400 if match is locked for predictions."""
    if match["status"] != "upcoming":
        raise HTTPException(status_code=400, detail="Predictions are locked — match is not upcoming.")
    kickoff = datetime.fromisoformat(match["kickoff_time"].replace("Z", "+00:00"))
    lock_time = kickoff - timedelta(minutes=LOCK_MINUTES_BEFORE)
    if datetime.now(timezone.utc) >= lock_time:
        raise HTTPException(status_code=400, detail="Predictions locked 5 minutes before kickoff.")


@router.post("")
def save_prediction(body: PredictionCreate, current_user: dict = Depends(get_current_user)):
    """Create or update a prediction. Locked 5 min before kickoff."""
    sb = get_supabase()

    # Fetch match
    match_result = safe_execute(sb.table("matches").select("*").eq("id", body.match_id).single())
    if not match_result.data:
        raise HTTPException(status_code=404, detail="Match not found")
    match = match_result.data
    _check_lock(match)

    # Check for existing prediction
    existing = safe_execute(
        sb.table("predictions")
        .select("id, is_locked")
        .eq("user_id", current_user["id"])
        .eq("match_id", body.match_id)
    )

    if existing.data:
        pred = existing.data[0]
        if pred.get("is_locked"):
            raise HTTPException(status_code=400, detail="Prediction is locked and cannot be updated.")
        # Update
        result = safe_execute(
            sb.table("predictions")
            .update({
                "predicted_team1_score": body.predicted_team1_score,
                "predicted_team2_score": body.predicted_team2_score,
                "prediction_time": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", pred["id"])
        )
    else:
        # Insert
        result = safe_execute(sb.table("predictions").insert({
            "user_id": current_user["id"],
            "match_id": body.match_id,
            "predicted_team1_score": body.predicted_team1_score,
            "predicted_team2_score": body.predicted_team2_score,
            "prediction_time": datetime.now(timezone.utc).isoformat(),
            "is_locked": False,
            "points_awarded": None,
        }))

    return result.data[0] if result.data else {"success": True}


@router.get("/my")
def my_predictions(current_user: dict = Depends(get_current_user)):
    """All predictions by the current user, joined with match info."""
    sb = get_supabase()
    result = safe_execute(
        sb.table("predictions")
        .select("*, matches(team1, team2, kickoff_time, stage, status, actual_team1_score, actual_team2_score, multiplier)")
        .eq("user_id", current_user["id"])
        .order("prediction_time", desc=True)
    )
    return result.data


@router.get("/match/{match_id}")
def predictions_for_match(match_id: str, current_user: dict = Depends(get_current_user)):
    """Current user's prediction for a specific match."""
    sb = get_supabase()
    result = safe_execute(
        sb.table("predictions")
        .select("*")
        .eq("user_id", current_user["id"])
        .eq("match_id", match_id)
    )
    return result.data[0] if result.data else None
