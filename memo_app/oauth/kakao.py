import os
import httpx
from fastapi import APIRouter, Request, Depends
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from dependencies import get_db
from sqlalchemy.orm import Session
from controllers import create_or_update_social_user
from fastapi.responses import RedirectResponse

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"

CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

@router.get("/auth/kakao/login")
def login():
    auth_url = (
        f"{KAKAO_AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=profile_nickname, account_email" # 동의항목: 카카오 디벨로퍼와 동일하게
    )
    return RedirectResponse(url=auth_url)

@router.get("/kakao/login/callback")
async def callback(request: Request, db: Session = Depends(get_db)):  # get_db() 사용
    code = request.query_params.get("code")
    
    async with httpx.AsyncClient() as client:
        token_res = await client.post(KAKAO_TOKEN_URL, data={
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
        userinfo_res = await client.get(KAKAO_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            return {"error": "Failed to retrieve user information"}

        # 사용자 정보 처리
        user_info_raw = userinfo_res.json()

        user_info = {
            "username": user_info_raw.get("properties", {}).get("nickname") or "User",
            "email": user_info_raw.get("kakao_account", {}).get("email"),
            "kakao_id": str(user_info_raw.get("id")) # 문자열로 형변환
        }

        user = create_or_update_social_user(db, user_info, provider='kakao')

        return templates.TemplateResponse("memos.html", {"request": request, "user_info": user})