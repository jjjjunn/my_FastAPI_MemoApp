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

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"

CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

@router.get("/auth/kakao/login")
async def login(request: Request):
    # CSRF 방지를 위한 state 토큰 생성
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    logger.info(f"생성된 state: {state}") # 상태 정보 로그
    logger.info(f"Session state stored: {request.session['oauth_state']}")  # state 값 저장 로그

    auth_url = (
        f"{KAKAO_AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/kakao/login/callback")
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
        token_res = await client.post(KAKAO_TOKEN_URL, data={
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'state': state,
        })
        
        if token_res.status_code != 200:
            logger.error(f"Token 요청 실패: {token_res.status_code}: {token_res.text}")
            return {"error": "Failed to retrieve token"}

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        # 사용자 정보 요청
        userinfo_res = await client.get(KAKAO_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            logger.error(f"사용자 정보 요청 실패: {userinfo_res.text}")
            return {"error": "Failed to retrieve user information"}

        # 사용자 정보 처리
        user_info_raw = userinfo_res.json()
        kakao_id = str(user_info_raw.get("id"))
        nickname = user_info_raw.get("properties", {}).get("nickname") or "User"
        email = user_info_raw.get("kakao_account", {}).get("email")

        # 필수 정보 확인
        if not kakao_id or not nickname:
            logger.error(f"유효하지 않은 사용자 정보: {user_info_raw}")
            return {"error": "Invalid user info"}

        user_info = {
            "username": nickname,
            "email": email,
            "kakao_id": kakao_id, # 문자열로 형변환
        }

        user = create_or_update_social_user(db, user_info, provider='kakao', request=request, access_token=access_token)

        # 로그인 후 세션에 정보 저장
        request.session["id"] = user.id  # 일반 사용자 ID
        request.session["username"] = user.username
        request.session["social_id"] = user_info["kakao_id"]  # 소셜 ID
        request.session["provider"] = 'kakao'  # 소셜 로그인 제공자
        request.session['access_token'] = access_token

    # 로그인 성공 후 메모 페이지로 이동
    return RedirectResponse(url="/memos")