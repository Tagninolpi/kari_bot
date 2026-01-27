from supabase import create_client, Client
import os
import datetime

# ---------------- CONFIG ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "KariGPT_requests"

# ---------------- Initialize Table ----------------
def initialize_table():
    """
    Checks if the table exists and has columns.
    Supabase doesn't allow dynamic column creation via API easily,
    so here we just make sure it exists by trying a query.
    If it fails, you must create the table manually in Supabase with columns:
      - id (UUID or SERIAL PRIMARY KEY)
      - user_id (BIGINT)
      - username (TEXT)
      - question (TEXT)
      - ai_response (TEXT)
      - timestamp (TIMESTAMP)
      - daily_limit (INT)
      - current_count (INT)
    """
    try:
        # Attempt a simple select
        supabase.table(TABLE_NAME).select("*").limit(1).execute()
        print(f"✅ Table '{TABLE_NAME}' exists")
    except Exception as e:
        print(f"❌ Table '{TABLE_NAME}' does not exist or is empty. Please create it manually.")
        print(e)

KariGPT_TZ = datetime.timezone(datetime.timedelta(hours=-8))

def now_utc8():
    return datetime.datetime.now(KariGPT_TZ)
# ---------------- Insert a new row ----------------
def insert_request(user_id, username, question, ai_response, daily_limit, current_count):
    now = now_utc8()

    # Store as UTC ISO (best practice for DBs)
    timestamp = now.astimezone(datetime.timezone.utc).isoformat()

    data = {
        "user_id": user_id,
        "username": username,
        "question": question,
        "ai_response": ai_response,
        "timestamp": timestamp,
        "daily_limit": daily_limit,
        "current_count": current_count
    }
    try:
        res = supabase.table(TABLE_NAME).insert(data).execute()
        print("📥 Inserted new KariGPT request:", res)
    except Exception as e:
        print("❌ Failed to insert request:", e)


# ---------------- Search previous questions ----------------
def find_previous_response(question: str):
    """
    Searches the table for an exact match of a question.
    Returns the ai_response if found, otherwise None.
    """
    try:
        res = supabase.table(TABLE_NAME).select("ai_response").eq("question", question).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["ai_response"]
        return None
    except Exception as e:
        print("❌ Failed to search previous questions:", e)
        return None
    
# ---------------- Get last request for a user ----------------
def get_last_request_for_user(user_id: int):
    """
    Returns the most recent request for the given user, or None if no request exists.
    """
    try:
        res = supabase.table(TABLE_NAME)\
            .select("*")\
            .eq("user_id", user_id)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()

        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print("❌ Failed to get last request for user:", e)
        return None

def generate_request_summary(now=None):
    """
    Returns a dictionary with KariGPT request metrics.
    All date logic is based on UTC+8.
    """
    try:
        if now is None:
            now = now_utc8()

        res = supabase.table(TABLE_NAME).select("*").execute()
        rows = res.data or []

        if not rows:
            return {"message": "No requests found in the database."}

        def to_utc8(ts_str):
            dt = datetime.datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(KariGPT_TZ)

        requests_by_day = {}
        requests_by_user = {}

        for row in rows:
            ts_utc8 = to_utc8(row["timestamp"])
            day_key = ts_utc8.date()
            requests_by_day.setdefault(day_key, []).append(row)

            uid = row["user_id"]
            requests_by_user.setdefault(uid, {"username": row["username"], "requests": []})
            requests_by_user[uid]["requests"].append(row)

        # Global stats
        total_requests = len(rows)
        total_days = len(requests_by_day)
        avg_requests_per_day = total_requests / total_days if total_days else 0
        max_requests_per_day = max(len(r) for r in requests_by_day.values())

        global_stats = {
            "total_requests": total_requests,
            "average_requests_per_day": round(avg_requests_per_day, 2),
            "max_requests_per_day": max_requests_per_day
        }

        # Per-player stats
        per_player_stats = {}
        for uid, info in requests_by_user.items():
            by_day = {}
            for r in info["requests"]:
                day = to_utc8(r["timestamp"]).date()
                by_day.setdefault(day, []).append(r)

            total_user = len(info["requests"])
            avg_user = total_user / len(by_day) if by_day else 0
            max_user = max(len(v) for v in by_day.values())

            per_player_stats[uid] = {
                "username": info["username"],
                "total_requests": total_user,
                "average_per_day": round(avg_user, 2),
                "max_requests_per_day": max_user
            }

        # Today (UTC+8)
        today_key = now.date()
        today_requests = requests_by_day.get(today_key, [])
        requests_per_user_today = {}

        for r in today_requests:
            uid = r["user_id"]
            requests_per_user_today.setdefault(uid, {
                "username": r["username"],
                "count": 0
            })
            requests_per_user_today[uid]["count"] += 1

        today_stats = {
            "total_requests_today": len(today_requests),
            "requests_per_user_today": requests_per_user_today
        }

        return {
            "global_stats": global_stats,
            "per_player_stats": per_player_stats,
            "today_stats": today_stats
        }

    except Exception as e:
        print("❌ Failed to generate request summary:", e)
        return None
