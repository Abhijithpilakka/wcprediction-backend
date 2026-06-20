from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import LoginRequest, AuthResponse
from app.core.supabase import get_supabase, safe_execute
from app.core.auth import create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    """
    Login or register a user with name + phone.
    - If phone exists → login (update name if changed)
    - Else → create new account
    Returns a JWT.
    """
    sb = get_supabase()

    # Check if phone exists
    result = safe_execute(sb.table("users").select("*").eq("phone_number", body.phone))
    existing = result.data

    if existing:
        user = existing[0]
        if user.get("is_banned"):
            raise HTTPException(status_code=403, detail="This account has been banned.")
        # Optionally update name
        if user["name"] != body.name:
            safe_execute(sb.table("users").update({"name": body.name}).eq("id", user["id"]))
            user["name"] = body.name
    else:
        # Create new user
        insert_result = safe_execute(sb.table("users").insert({
            "name": body.name,
            "phone_number": body.phone,
            "total_points": 0,
            "weekly_points": 0,
            "exact_predictions": 0,
            "is_admin": False,
            "is_banned": False,
        }))
        user = insert_result.data[0]

    token = create_token(user["id"])
    return {"token": token, "user": user}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
