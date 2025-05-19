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

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USERINFO_URL = "https://openapi.naver.com/v1/nid/me"

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")

@router.get("/auth/naver/login")
async def login(request: Request):
    # CSRF 방지를 위한 state 토큰 생성
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    logger.info(f"생성된 state: {state}") # 상태 정보 로그
    logger.info(f"Session state stored: {request.session['oauth_state']}")  # state 값 저장 로그

    auth_url = (
        f"{NAVER_AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url, status_code=302) # 일시 리디렉션

@router.get("/naver/login/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    session_state = request.session.get("oauth_state")

    # CSRF 방지: state 검증
    logger.info(f"Session state: {session_state}, Callback state: {state}")
    if state != session_state:
        logger.warning("State Mismatch")
        raise HTTPException(status_code=400, detail="Invalid OAuth State")

    async with httpx.AsyncClient() as client:
        # 액세스 토큰 요청
        token_res = await client.post(NAVER_TOKEN_URL, data={
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'state': state,
        })

        if token_res.status_code != 200:
            logger.error(f"Token 요청 실패: {token_res.status_code}, 내용: {token_res.text}")
            return RedirectResponse(url="/login?error=token")

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        if not access_token:
            logger.error(f"access_token 없음. 응답 내용: {token_data}")
            return RedirectResponse(url="/login?error=no_token")

        # 사용자 정보 요청
        userinfo_res = await client.get(NAVER_USERINFO_URL, headers={
            'Authorization': f'Bearer {access_token}'
        })

        if userinfo_res.status_code != 200:
            logger.error(f"사용자 정보 요청 실패: {userinfo_res.text}")
            return RedirectResponse(url="/login?error=userinfo")

        user_info_raw = userinfo_res.json()
        naver_response = user_info_raw.get("response", {})

        if not naver_response.get("email") or not naver_response.get("id"):
            logger.error(f"유효하지 않은 사용자 정보: {naver_response}")
            return RedirectResponse(url="/login?error=invalid_user")

        # 사용자 정보 정리
        user_info = {
            "username": naver_response.get("name") or "User",
            "email": naver_response.get("email"),
            "naver_id": naver_response.get("id")
        }

        # DB에 유저 저장 또는 업데이트
        user = create_or_update_social_user(db, user_info, provider='naver', request=request, access_token=access_token)

        # 세션에 로그인 정보 저장
        request.session["id"] = user.id
        request.session["username"] = user.username
        request.session["social_id"] = user_info["naver_id"]
        request.session["provider"] = 'naver'
        request.session['access_token'] = access_token

        logger.info(f"소셜 로그인 성공: {user.username}")

    # 로그인 성공 후 메모 페이지로 이동
    return RedirectResponse(url="/memos")