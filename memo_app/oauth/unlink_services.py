import os
import httpx
from fastapi import APIRouter, Request, Depends, HTTPException
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from dependencies import get_db
import logging

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 구글 연결 해제
@router.post("/unlink/google")
async def google_unlink(access_token: str):
    url = f"https://oauth2.googleapis.com/revoke?token={access_token}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)

    # if response.status_code == 200:
    #     return {"message": "Google 연결 해제 완료"}
    # else:
    #     raise HTTPException(status_code=400, detail="Google 연결 해제 실패")
    
    return response

# 카카오 연결 해제
@router.post("/unlink/kakao")
async def kakao_unlink(access_token: str):
    url = "https://kapi.kakao.com/v1/user/unlink"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)

    # if response.status_code == 200:
    #     return {"message": "Kakao 연결 해제 완료"}
    # else:
    #     raise HTTPException(status_code=400, detail="Kakao 연결 해제 실패")
    
    return response


# 네이버 연결 해제
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

@router.post("/unlink/naver")
async def naver_unlink(access_token: str):
    url = "https://nid.naver.com/oauth2.0/token"
    params = {
        "grant_type": "delete",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "access_token": access_token,
        "service_provider": "NAVER"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params)

    # if response.status_code == 200:
    #     return {"message": "NAVER 연결 해제 완료"}
    # else:
    #     raise HTTPException(status_code=400, detail="NAVER 연결 해제 실패")
    
    return response

# 소셜 연동 해제 함수
async def social_unlink_task(provider: str, access_token):
    try:
        if provider == "google":
            result = await google_unlink(access_token=access_token)

        elif provider == "kakao":
            result = await kakao_unlink(access_token=access_token)

        elif provider == "naver":
            result = await naver_unlink(access_token=access_token)

        else:
            logger.warning(f"지원하지 않는 제공자: {provider}, 연결 해제 생략.")
            result = None
    
        if result and result.status_code == 200:
            logger.info("소셜 연결 해제 성공")
        else:
            logger.warning(f"{provider} 연동 해제 실패: {result.status_code} - {result.text}")
    except Exception as e:
        logger.error(f"{provider} 연동 해제 중 에러 발생: {e}")
    