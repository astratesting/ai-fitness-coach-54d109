"""AI Fitness Coach backend API.

FastAPI service for personalized workout plans, nutrition tracking,
AI coaching, progress tracking, and Clerk-authenticated users.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import asyncpg
import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from pydantic import BaseModel, ConfigDict, Field, field_validator

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fitness_coach")
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", f"{CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json" if CLERK_ISSUER else "")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

ALLOWED_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGIN.split(",") if origin.strip()]


class UserProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=18, le=80)
    height_cm: int = Field(ge=120, le=230)
    weight_kg: float = Field(gt=35, le=250)
    goal: Literal["fat_loss", "muscle_gain", "strength", "endurance", "general_fitness"]
    fitness_level: Literal["beginner", "intermediate", "advanced"]
    schedule_minutes: int = Field(ge=10, le=120)
    workouts_per_week: int = Field(ge=1, le=7)
    dietary_preference: Literal["standard", "vegetarian", "vegan", "pescatarian", "keto", "mediterranean"] = "standard"
    injuries: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Invalid email address")
        return value.lower()


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=18, le=80)
    height_cm: int | None = Field(default=None, ge=120, le=230)
    weight_kg: float | None = Field(default=None, gt=35, le=250)
    goal: Literal["fat_loss", "muscle_gain", "strength", "endurance", "general_fitness"] | None = None
    fitness_level: Literal["beginner", "intermediate", "advanced"] | None = None
    schedule_minutes: int | None = Field(default=None, ge=10, le=120)
    workouts_per_week: int | None = Field(default=None, ge=1, le=7)
    dietary_preference: Literal["standard", "vegetarian", "vegan", "pescatarian", "keto", "mediterranean"] | None = None
    injuries: list[str] | None = Field(default=None, max_length=10)


class WorkoutPlanRequest(BaseModel):
    focus: Literal["full_body", "upper_body", "lower_body", "cardio", "mobility", "strength"] = "full_body"
    available_equipment: list[str] = Field(default_factory=list, max_length=20)
    days: int = Field(default=7, ge=1, le=14)


class NutritionLogRequest(BaseModel):
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    description: str = Field(min_length=2, max_length=2000)
    calories: int = Field(ge=0, le=5000)
    protein_g: float = Field(ge=0, le=400)
    carbs_g: float = Field(ge=0, le=800)
    fat_g: float = Field(ge=0, le=400)


class ProgressEntryRequest(BaseModel):
    recorded_on: date = Field(default_factory=date.today)
    weight_kg: float | None = Field(default=None, gt=35, le=250)
    body_fat_percent: float | None = Field(default=None, ge=3, le=70)
    resting_heart_rate: int | None = Field(default=None, ge=35, le=140)
    steps: int | None = Field(default=None, ge=0, le=100000)
    workout_minutes: int | None = Field(default=None, ge=0, le=600)
    mood: Literal["low", "okay", "good", "great"] | None = None
    notes: str | None = Field(default=None, max_length=1000)


class CoachingRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


class AuthUser(BaseModel):
    user_id: str
    email: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str
    time: datetime


class ApiResponse(BaseModel):
    data: Any


class AppState:
    pool: asyncpg.Pool | None = None
    jwks_client: PyJWKClient | None = None


state = AppState()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 80),
    height_cm INTEGER NOT NULL CHECK (height_cm BETWEEN 120 AND 230),
    weight_kg NUMERIC(6,2) NOT NULL CHECK (weight_kg > 35 AND weight_kg <= 250),
    goal TEXT NOT NULL,
    fitness_level TEXT NOT NULL,
    schedule_minutes INTEGER NOT NULL CHECK (schedule_minutes BETWEEN 10 AND 120),
    workouts_per_week INTEGER NOT NULL CHECK (workouts_per_week BETWEEN 1 AND 7),
    dietary_preference TEXT NOT NULL DEFAULT 'standard',
    injuries JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    focus TEXT NOT NULL,
    available_equipment JSONB NOT NULL DEFAULT '[]'::jsonb,
    plan JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS nutrition_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at TIMESTAMPTZ NOT NULL,
    meal_type TEXT NOT NULL,
    description TEXT NOT NULL,
    calories INTEGER NOT NULL CHECK (calories >= 0 AND calories <= 5000),
    protein_g NUMERIC(7,2) NOT NULL CHECK (protein_g >= 0),
    carbs_g NUMERIC(7,2) NOT NULL CHECK (carbs_g >= 0),
    fat_g NUMERIC(7,2) NOT NULL CHECK (fat_g >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS progress_entries (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recorded_on DATE NOT NULL,
    weight_kg NUMERIC(6,2),
    body_fat_percent NUMERIC(5,2),
    resting_heart_rate INTEGER,
    steps INTEGER,
    workout_minutes INTEGER,
    mood TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, recorded_on)
);

CREATE INDEX IF NOT EXISTS idx_workout_plans_user_created ON workout_plans(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nutrition_logs_user_logged ON nutrition_logs(user_id, logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_progress_entries_user_recorded ON progress_entries(user_id, recorded_on DESC);
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10, command_timeout=30)
    async with state.pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
    if CLERK_JWKS_URL:
        state.jwks_client = PyJWKClient(CLERK_JWKS_URL)
    yield
    if state.pool:
        await state.pool.close()


app = FastAPI(
    title="AI Fitness Coach API",
    version="1.0.0",
    description="Backend API for AI fitness coaching MVP.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "svix-id", "svix-timestamp", "svix-signature"],
)


def require_pool() -> asyncpg.Pool:
    if not state.pool:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return state.pool


def encode_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def row_to_dict(row: asyncpg.Record | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
    return result


def rows_to_dicts(rows: list[asyncpg.Record]) -> list[dict[str, Any]]:
    return [row_to_dict(row) or {} for row in rows]


async def get_current_user(authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if ENVIRONMENT == "development" and token.startswith("dev:"):
        user_id = token.removeprefix("dev:").strip()
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid development token")
        return AuthUser(user_id=user_id, email=f"{user_id}@example.com")

    if not state.jwks_client or not CLERK_ISSUER:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication provider not configured")

    try:
        signing_key = state.jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    email = claims.get("email")
    return AuthUser(user_id=user_id, email=email if isinstance(email, str) else None)


async def ensure_user_exists(conn: asyncpg.Connection, user: AuthUser) -> dict[str, Any]:
    row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user.user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return row_to_dict(row) or {}


def calculate_targets(profile: dict[str, Any]) -> dict[str, int]:
    weight = float(profile["weight_kg"])
    height = int(profile["height_cm"])
    age = int(profile["age"])
    minutes = int(profile["schedule_minutes"])
    workouts = int(profile["workouts_per_week"])
    goal = profile["goal"]

    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    activity_multiplier = 1.2 + min(workouts * minutes / 900, 0.55)
    maintenance = int(bmr * activity_multiplier)
    calorie_delta = {
        "fat_loss": -400,
        "muscle_gain": 250,
        "strength": 100,
        "endurance": 100,
        "general_fitness": 0,
    }[goal]
    calories = max(1200, maintenance + calorie_delta)
    protein = int(weight * (2.0 if goal in {"fat_loss", "muscle_gain", "strength"} else 1.6))
    fat = int((calories * 0.25) / 9)
    carbs = int(max(0, (calories - protein * 4 - fat * 9) / 4))
    return {"calories": calories, "protein_g": protein, "carbs_g": carbs, "fat_g": fat}


def generate_rule_based_workout(profile: dict[str, Any], request: WorkoutPlanRequest) -> dict[str, Any]:
    level = profile["fitness_level"]
    minutes = int(profile["schedule_minutes"])
    sessions = min(int(profile["workouts_per_week"]), request.days)
    injuries = profile.get("injuries") or []
    equipment = request.available_equipment or ["bodyweight"]

    intensity = {"beginner": "moderate", "intermediate": "challenging", "advanced": "high"}[level]
    rounds = {"beginner": 2, "intermediate": 3, "advanced": 4}[level]
    reps = {"beginner": "8-10", "intermediate": "10-12", "advanced": "12-15"}[level]

    movement_library = {
        "full_body": ["squat", "push-up", "hip hinge", "row", "plank"],
        "upper_body": ["push-up", "row", "shoulder press", "curl", "triceps extension"],
        "lower_body": ["squat", "lunge", "glute bridge", "calf raise", "deadlift pattern"],
        "cardio": ["brisk walk", "bike intervals", "jumping jacks", "mountain climbers", "step-ups"],
        "mobility": ["world's greatest stretch", "cat-cow", "hip flexor stretch", "thoracic rotation", "hamstring floss"],
        "strength": ["squat", "deadlift pattern", "press", "row", "loaded carry"],
    }
    movements = movement_library[request.focus]

    sessions_list = []
    for index in range(sessions):
        sessions_list.append(
            {
                "day": index + 1,
                "duration_minutes": minutes,
                "focus": request.focus,
                "warmup": ["5 min easy cardio", "dynamic mobility", "activation drills"],
                "main_set": [
                    {"exercise": movement, "sets": rounds, "reps": reps, "rest_seconds": 60}
                    for movement in movements
                ],
                "finisher": "6 min steady zone 2" if request.focus != "mobility" else "5 min breathing reset",
                "cooldown": ["easy walk", "stretch worked muscles", "log effort 1-10"],
            }
        )

    return {
        "summary": f"{sessions}-session {intensity} {request.focus.replace('_', ' ')} plan for busy schedule.",
        "equipment": equipment,
        "injury_modifications": injuries,
        "weekly_sessions": sessions_list,
        "progression": "Add one rep per set next week, then add load or one extra round when all reps feel controlled.",
    }


async def generate_ai_text(system_prompt: str, user_prompt: str) -> str:
    if not OPENAI_API_KEY:
        return ""

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 700,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()


async def generate_coaching_reply(profile: dict[str, Any], message: str, context: dict[str, Any]) -> str:
    fallback = (
        "Small next step: pick one action you can finish today. "
        f"Given your {profile['goal'].replace('_', ' ')} goal and {profile['schedule_minutes']}-minute window, "
        "prioritize consistency, protein, hydration, and sleep."
    )
    ai_text = await generate_ai_text(
        "You are a safe, evidence-informed fitness coach for busy professionals. Give concise, actionable guidance. Never diagnose or prescribe medical treatment.",
        encode_json({"profile": profile, "message": message, "context": context}),
    )
    return ai_text or fallback


def verify_svix_signature(payload: bytes, svix_id: str | None, svix_timestamp: str | None, svix_signature: str | None) -> None:
    if not CLERK_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook secret not configured")
    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Svix headers")

    try:
        timestamp = int(svix_timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Svix timestamp") from exc
    if abs(time.time() - timestamp) > 300:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stale webhook timestamp")

    signed_content = f"{svix_id}.{svix_timestamp}.".encode() + payload
    secret = CLERK_WEBHOOK_SECRET.removeprefix("whsec_").encode()
    expected = hmac.new(secret, signed_content, hashlib.sha256).digest()

    signatures = [part.split(",")[-1] for part in svix_signature.split(" ") if part]
    expected_hex = expected.hex()
    if not any(hmac.compare_digest(expected_hex, signature) for signature in signatures):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=ENVIRONMENT, time=datetime.now(timezone.utc))


@app.get("/me", response_model=ApiResponse)
async def get_me(user: AuthUser = Depends(get_current_user), pool: asyncpg.Pool = Depends(require_pool)) -> ApiResponse:
    async with pool.acquire() as conn:
        profile = await ensure_user_exists(conn, user)
    profile["targets"] = calculate_targets(profile)
    return ApiResponse(data=profile)


@app.post("/me", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_or_replace_profile(
    profile: UserProfile,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (
                id, email, name, age, height_cm, weight_kg, goal, fitness_level,
                schedule_minutes, workouts_per_week, dietary_preference, injuries, updated_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,now())
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                age = EXCLUDED.age,
                height_cm = EXCLUDED.height_cm,
                weight_kg = EXCLUDED.weight_kg,
                goal = EXCLUDED.goal,
                fitness_level = EXCLUDED.fitness_level,
                schedule_minutes = EXCLUDED.schedule_minutes,
                workouts_per_week = EXCLUDED.workouts_per_week,
                dietary_preference = EXCLUDED.dietary_preference,
                injuries = EXCLUDED.injuries,
                updated_at = now()
            RETURNING *
            """,
            user.user_id,
            profile.email,
            profile.name,
            profile.age,
            profile.height_cm,
            profile.weight_kg,
            profile.goal,
            profile.fitness_level,
            profile.schedule_minutes,
            profile.workouts_per_week,
            profile.dietary_preference,
            encode_json(profile.injuries),
        )
    data = row_to_dict(row) or {}
    data["targets"] = calculate_targets(data)
    return ApiResponse(data=data)


@app.put("/me", response_model=ApiResponse)
async def update_profile(
    updates: ProfileUpdate,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No updates provided")

    allowed = {
        "name",
        "age",
        "height_cm",
        "weight_kg",
        "goal",
        "fitness_level",
        "schedule_minutes",
        "workouts_per_week",
        "dietary_preference",
        "injuries",
    }
    set_parts = []
    values: list[Any] = []
    for index, (key, value) in enumerate(update_data.items(), start=2):
        if key not in allowed:
            continue
        if key == "injuries":
            set_parts.append(f"{key} = ${index}::jsonb")
            values.append(encode_json(value))
        else:
            set_parts.append(f"{key} = ${index}")
            values.append(value)

    query = f"UPDATE users SET {', '.join(set_parts)}, updated_at = now() WHERE id = $1 RETURNING *"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, user.user_id, *values)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    data = row_to_dict(row) or {}
    data["targets"] = calculate_targets(data)
    return ApiResponse(data=data)


@app.post("/workout-plans", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_workout_plan(
    request: WorkoutPlanRequest,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    async with pool.acquire() as conn:
        profile = await ensure_user_exists(conn, user)
        plan = generate_rule_based_workout(profile, request)
        row = await conn.fetchrow(
            """
            INSERT INTO workout_plans (user_id, focus, available_equipment, plan)
            VALUES ($1, $2, $3::jsonb, $4::jsonb)
            RETURNING *
            """,
            user.user_id,
            request.focus,
            encode_json(request.available_equipment),
            encode_json(plan),
        )
    return ApiResponse(data=row_to_dict(row))


@app.get("/workout-plans", response_model=ApiResponse)
async def list_workout_plans(
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
    limit: int = Query(default=10, ge=1, le=50),
) -> ApiResponse:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM workout_plans WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            user.user_id,
            limit,
        )
    return ApiResponse(data=rows_to_dicts(rows))


@app.post("/nutrition", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def log_nutrition(
    request: NutritionLogRequest,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    async with pool.acquire() as conn:
        await ensure_user_exists(conn, user)
        row = await conn.fetchrow(
            """
            INSERT INTO nutrition_logs (user_id, logged_at, meal_type, description, calories, protein_g, carbs_g, fat_g)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            RETURNING *
            """,
            user.user_id,
            request.logged_at,
            request.meal_type,
            request.description,
            request.calories,
            request.protein_g,
            request.carbs_g,
            request.fat_g,
        )
    return ApiResponse(data=row_to_dict(row))


@app.get("/nutrition", response_model=ApiResponse)
async def list_nutrition(
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
    days: int = Query(default=7, ge=1, le=90),
) -> ApiResponse:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM nutrition_logs WHERE user_id = $1 AND logged_at >= $2 ORDER BY logged_at DESC",
            user.user_id,
            since,
        )
        totals = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(calories),0)::int AS calories,
                   COALESCE(SUM(protein_g),0)::float AS protein_g,
                   COALESCE(SUM(carbs_g),0)::float AS carbs_g,
                   COALESCE(SUM(fat_g),0)::float AS fat_g
            FROM nutrition_logs WHERE user_id = $1 AND logged_at >= $2
            """,
            user.user_id,
            since,
        )
    return ApiResponse(data={"items": rows_to_dicts(rows), "totals": row_to_dict(totals)})


@app.post("/progress", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def upsert_progress(
    request: ProgressEntryRequest,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    async with pool.acquire() as conn:
        await ensure_user_exists(conn, user)
        row = await conn.fetchrow(
            """
            INSERT INTO progress_entries (
                user_id, recorded_on, weight_kg, body_fat_percent, resting_heart_rate,
                steps, workout_minutes, mood, notes
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (user_id, recorded_on) DO UPDATE SET
                weight_kg = EXCLUDED.weight_kg,
                body_fat_percent = EXCLUDED.body_fat_percent,
                resting_heart_rate = EXCLUDED.resting_heart_rate,
                steps = EXCLUDED.steps,
                workout_minutes = EXCLUDED.workout_minutes,
                mood = EXCLUDED.mood,
                notes = EXCLUDED.notes
            RETURNING *
            """,
            user.user_id,
            request.recorded_on,
            request.weight_kg,
            request.body_fat_percent,
            request.resting_heart_rate,
            request.steps,
            request.workout_minutes,
            request.mood,
            request.notes,
        )
    return ApiResponse(data=row_to_dict(row))


@app.get("/progress", response_model=ApiResponse)
async def list_progress(
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
    days: int = Query(default=30, ge=1, le=365),
) -> ApiResponse:
    since = date.today() - timedelta(days=days)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM progress_entries WHERE user_id = $1 AND recorded_on >= $2 ORDER BY recorded_on DESC",
            user.user_id,
            since,
        )
    return ApiResponse(data=rows_to_dicts(rows))


@app.post("/coach", response_model=ApiResponse)
async def coach(
    request: CoachingRequest,
    user: AuthUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    async with pool.acquire() as conn:
        profile = await ensure_user_exists(conn, user)
        recent_progress = await conn.fetch(
            "SELECT * FROM progress_entries WHERE user_id = $1 ORDER BY recorded_on DESC LIMIT 5",
            user.user_id,
        )
        recent_nutrition = await conn.fetch(
            "SELECT * FROM nutrition_logs WHERE user_id = $1 ORDER BY logged_at DESC LIMIT 5",
            user.user_id,
        )

    context = {
        **request.context,
        "recent_progress": rows_to_dicts(recent_progress),
        "recent_nutrition": rows_to_dicts(recent_nutrition),
        "targets": calculate_targets(profile),
    }
    reply = await generate_coaching_reply(profile, request.message, context)
    return ApiResponse(data={"reply": reply, "context_used": context})


@app.post("/webhooks/clerk", response_model=ApiResponse)
async def clerk_webhook(
    request: Request,
    svix_id: str | None = Header(default=None),
    svix_timestamp: str | None = Header(default=None),
    svix_signature: str | None = Header(default=None),
    pool: asyncpg.Pool = Depends(require_pool),
) -> ApiResponse:
    payload = await request.body()
    verify_svix_signature(payload, svix_id, svix_timestamp, svix_signature)
    event = json.loads(payload)
    event_type = event.get("type")
    data = event.get("data") or {}
    user_id = data.get("id")

    if not isinstance(user_id, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Clerk event")

    async with pool.acquire() as conn:
        if event_type == "user.deleted":
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
            return ApiResponse(data={"deleted": user_id})

    return ApiResponse(data={"received": event_type})


@app.delete("/me", response_model=ApiResponse)
async def delete_me(user: AuthUser = Depends(get_current_user), pool: asyncpg.Pool = Depends(require_pool)) -> ApiResponse:
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM users WHERE id = $1", user.user_id)
    return ApiResponse(data={"result": result})
