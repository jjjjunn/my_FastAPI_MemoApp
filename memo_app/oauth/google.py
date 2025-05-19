import os
import httpx
from fastapi import APIRouter, Request, Depends, HTTPException
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from dependencies import get_db
from sqlalchemy.orm import Session
from controllers.users_controller import create_or_update_social_user
from fastapi.responses import RedirectResponse
import secrets
import logging

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

@router.get("/auth/google/login")
async def login(request: Request):
    # CSRF 방지를 위한 state 토큰 생성
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    logger.info(f"생성된 state: {state}") # 상태 정보 로그
    logger.info(f"Session state stored: {request.session['oauth_state']}")  # state 값 저장 로그

    auth_url = (
        f"{GOOGLE_AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/auth/google/callback")
async def callback(request: Request, db: Session = Depends(get_db)):  # get_db() 사용
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    session_state = request.session.get("oauth_state")

    # CSRF 방지: state 검증
    logger.info(f"Session state: {session_state}, Callback state: {state}")  # 디버깅 로그
    if state != session_state:
        logger.warning("State Mismatch")
        raise HTTPException(status_code=400, detail="Invalid OAuth State")
    
    async with httpx.AsyncClient() as client:
        token_res = await client.post(GOOGLE_TOKEN_URL, data={
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
        }) # 'state': state, 구글 토큰에 요청 불가
        
        if token_res.status_code != 200:
            logger.error(f"Token 요청 실패: {token_res.status_code}: {token_res.text}")
            return {"error": "Failed to retrieve token"}

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        # 사용자 정보 요청
        userinfo_res = await client.get(GOOGLE_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            logger.error(f"사용자 정보 요청 실패: {userinfo_res.text}")
            return {"error": "Failed to retrieve user information"}

        # 사용자 정보 처리
        user_info_raw = userinfo_res.json()
        google_id = str(user_info_raw.get("id"))
        username = user_info_raw.get("name") or "User" # 이름이 없을 경우 기본값 설정
        email = user_info_raw.get("email")

        # 필수 정보 확인
        if not google_id or not username:
            logger.error(f"유효하지 않은 사용자 정보: {user_info_raw}")
            return {"error": "Invalid user info"}
        
        user_info = {
            "username" : username,  
            "email" : email,
            "google_id" : google_id,
        }

        user = create_or_update_social_user(db, user_info, provider='google', request=request, access_token=access_token)
        # 로그인 후 세션에 정보 저장
        request.session["id"] = user.id  # 일반 사용자 ID
        request.session["username"] = user.username
        request.session["social_id"] = user_info["google_id"]  # 소셜 ID
        request.session["provider"] = 'google'  # 소셜 로그인 제공자
        request.session['access_token'] = access_token

    # 로그인 성공 후 메모 페이지로 이동
    return RedirectResponse(url="/memos")
    
