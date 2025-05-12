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

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USERINFO_URL = "https://openapi.naver.com/v1/nid/me"

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")

@router.get("/auth/naver/login")
def login():
    auth_url = (
        f"{NAVER_AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=email, id"
    )
    return RedirectResponse(url=auth_url)

@router.get("/naver/login/callback")
async def callback(request: Request, db: Session = Depends(get_db)):  # get_db() 사용
    code = request.query_params.get("code")
    
    async with httpx.AsyncClient() as client:
        token_res = await client.post(NAVER_TOKEN_URL, data={
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
        userinfo_res = await client.get(NAVER_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            return {"error": "Failed to retrieve user information"}

        # 사용자 정보 처리
        user_info_raw = userinfo_res.json()
        naver_response = user_info_raw.get("response", {})
        user_info = {
            "username": naver_response.get("name") or "User",  # 이름 없으면 기본값
            "email" : naver_response.get("email"),
            "naver_id" : naver_response.get("id")
        }

        user = create_or_update_social_user(db, user_info, provider='naver')

        return templates.TemplateResponse("memos.html", {"request": request, "user_info": user})