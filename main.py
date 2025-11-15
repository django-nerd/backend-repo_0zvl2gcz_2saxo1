import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers to load local JSON files ----------
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(BACKEND_DIR, "profile.json")
DIARY_PATH = os.path.join(BACKEND_DIR, "diary.json")


def read_json_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- Models (for documentation) ----------
class SocialLink(BaseModel):
    label: str
    url: str

class Profile(BaseModel):
    name: str
    photo_url: str
    tagline: Optional[str] = None
    socials: List[SocialLink]

class DiaryItem(BaseModel):
    id: str
    title: str
    date: str  # ISO date string
    summary: Optional[str] = None
    content: Optional[str] = None


# ---------- Routes ----------
@app.get("/")
def read_root():
    return {"message": "Portfolio Backend Running"}

@app.get("/api/profile", response_model=Profile)
def get_profile():
    try:
        data = read_json_file(PROFILE_PATH)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="profile.json not found. Add it to the backend root.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diary", response_model=List[DiaryItem])
def list_diary():
    try:
        data = read_json_file(DIARY_PATH)
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, list):
            return data
        return []
    except FileNotFoundError:
        # Empty list if not created yet
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diary/{item_id}", response_model=DiaryItem)
def get_diary_item(item_id: str):
    try:
        items = list_diary()
        for item in items:
            if item.get("id") == item_id:
                return item
        raise HTTPException(status_code=404, detail="Diary item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
