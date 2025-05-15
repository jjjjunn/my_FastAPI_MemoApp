from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Depends, APIRouter

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 라우트
@router.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})

# 'About' 페이지 추가
@router.get('/about')
async def about():
    return {"message": "메모 앱 소개 페이지 입니다."}