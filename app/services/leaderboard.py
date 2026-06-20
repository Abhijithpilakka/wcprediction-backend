"""
Leaderboard service.
Computes and stores leaderboard snapshots in Supabase.
Called after every result update.
"""
from datetime import datetime, timezone
from app.core.supabase import get_supabase, safe_execute


def get_current_week() -> int:
    """ISO week number — used to bucket weekly points."""
    return datetime.now(timezone.utc).isocalendar()[1]


def recompute_overall(sb=None):
    """Recompute overall leaderboard from users table."""
    if sb is None:
        sb = get_supabase()

    users = safe_execute(sb.table("users").select("id, total_points, exact_predictions")).data
    if not users:
        return

    # Sort: total_points desc, exact_predictions desc
    ranked = sorted(users, key=lambda u: (-u["total_points"], -u["exact_predictions"]))

    rows = []
    for rank, u in enumerate(ranked, start=1):
        rows.append({
            "user_id": u["id"],
            "points": u["total_points"],
            "rank": rank,
            "exact_scores": u["exact_predictions"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    # Upsert (on user_id conflict)
    if rows:
        safe_execute(sb.table("overall_leaderboard").upsert(rows, on_conflict="user_id"))


def recompute_weekly(sb=None):
    """Recompute weekly leaderboard from users table."""
    if sb is None:
        sb = get_supabase()

    week = get_current_week()
    users = safe_execute(sb.table("users").select("id, weekly_points")).data
    if not users:
        return

    ranked = sorted(users, key=lambda u: -u["weekly_points"])

    rows = []
    for rank, u in enumerate(ranked, start=1):
        rows.append({
            "week_number": week,
            "user_id": u["id"],
            "points": u["weekly_points"],
            "rank": rank,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    if rows:
        safe_execute(sb.table("weekly_leaderboard").upsert(
            rows, on_conflict="week_number,user_id"
        ))


def recompute_all(sb=None):
    if sb is None:
        sb = get_supabase()
    recompute_overall(sb)
    recompute_weekly(sb)
