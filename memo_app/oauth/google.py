import os
import httpx
from fastapi import APIRouter, Request, Depends
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from dependencies import get_db
from sqlalchemy.orm import Session
from controllers import create_or_update_user

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

@router.get("/auth/google/login")
def login():
    return {
        "auth_url": f"{GOOGLE_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile"
    }

@router.get("/auth/google/callback")
async def callback(request: Request, db: Session = Depends(get_db)):  # get_db() 사용
    code = request.query_params.get("code")
    
    async with httpx.AsyncClient() as client:
        token_res = await client.post(GOOGLE_TOKEN_URL, data={
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        })
        
        if token_res.status_code != 200:
            return {"error": "Failed to retrieve token"}

        access_token = token_res.json().get("access_token")

        # 사용자 정보 요청
        userinfo_res = await client.get(GOOGLE_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            return {"error": "Failed to retrieve user information"}

        # 사용자 정보 처리
        user_info = userinfo_res.json()
        username = user_info.get("name") if user_info.get("name") else "User"  # 이름이 없을 경우 기본값 설정
        email = user_info.get("email")
        google_id = user_info.get("id")

        user = create_or_update_user(db, {  # db를 사용하여 사용자 정보 처리
            "username": username,
            "email": email,
            "google_id": google_id
        })

        return templates.TemplateResponse("memos.html", {"request": request, "user_info": user})