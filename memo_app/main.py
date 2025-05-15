from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from controllers.users_controller import router as users_router  # USER 컨트롤러 라우터 import
from controllers.memos_controller import router as memos_router  # Memo 컨트롤러 라우터 import
from oauth.unlink_services import router as unlink_router # 소셜 연동 해제 라우터 import
from database import Base, engine # 데이터베이스 설정 import
from starlette.middleware.sessions import SessionMiddleware
from oauth import google, kakao, naver
import logging
from fastapi.responses import HTMLResponse

# FastAPI 애플리케이션 생성
app = FastAPI()
app.add_middleware(
    SessionMiddleware, 
    secret_key="your-secret-key",
    max_age=60 * 60,  # 1시간 후 세션 만료
    same_site="lax", # same_site가 없으면 세션 쿠키가 인증 흐름 중 브라우저에서 차단될 수 있음
    https_only=False, # 로컬 환경에서 HTTPS가 아니라면, 브라우저가 Secure 속성이 있는 쿠키를 저장하지 않을 수 있으므로, https_only=False
    session_cookie="session",
)

templates = Jinja2Templates(directory="templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # 로깅 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger = logging.getLogger(__name__)

# 템플릿 디렉터리 설정
templates = Jinja2Templates(directory="templates")

# 라우터 포함
app.include_router(users_router, tags=["users"])  # USERS 라우터 포함
app.include_router(memos_router, tags=["memos"])  # MEMOS 라우터 포함
app.include_router(unlink_router, tags=["social_unlink"]) # 소셜 연동 해제 라우터 포함
app.include_router(google.router) # Google OAuth2 라우터 포함
app.include_router(kakao.router) # KAKAO OAuth2 라우터 포함
app.include_router(naver.router) # NAVER OAuth2 라우터 포함

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 홈페이지
@app.get('/')
async def read_root(request: Request):
    logger.info("홈페이지 요청 수신")
    return templates.TemplateResponse('login.html', {"request": request})

# 회원 가입 페이지 엔드 포인트
@app.get('/signup', response_class=HTMLResponse)
async def sign_up(request: Request):
    logger.info("회원가입 페이지 요청 수신")
    return templates.TemplateResponse('signup.html', {"request": request})

# 로그아웃
@app.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 완료!"}

# 아이디 비밀번호 찾기 페이지 엔드포인트
@app.get("/find_account", response_class=HTMLResponse)
async def read_find_id(request: Request):
    logger.info("아이디/비밀번호 찾기 페이지 요청 수신")
    return templates.TemplateResponse('find_account.html', {"request": request})

# 비밀번호 변경하기 페이지 엔드포인트
@app.get("/change_pw", response_class=HTMLResponse)
async def read_change_pw(request: Request):
    logger.info("비밀번호 변경 페이지 요청 수신")
    return templates.TemplateResponse('change_pw.html', {"request": request})