from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from controllers import router # 컨트롤러 라우터 import
from database import Base, engine # 데이터베이스 설정 import
from starlette.middleware.sessions import SessionMiddleware
from oauth import google

# FastAPI 애플리케이션 생성
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")

# 템플릿 디렉터리 설정
templates = Jinja2Templates(directory="templates")

# 라우터 포함
app.include_router(router)
app.include_router(google.router) # Google OAuth2 라우터 포함

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

@router.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})