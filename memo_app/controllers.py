from fastapi import FastAPI, Request, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from models import User, Memo # 모델 import
from schemas import UserCreate, UserLogin, MemoCreate, MemoUpdate # 스키마 import
from dependencies import get_db, get_password_hash, verify_password # 의존성 import
from fastapi.templating import Jinja2Templates
import re

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 회원 가입
@router.post("/signup")
async def signup(signup_data: UserCreate, db: Session=Depends(get_db)):
    # ID 규칙 확인: 영어 소문자와 숫자만 허용
    if not re.fullmatch(r"[a-z0-9]+", signup_data.username):
        raise HTTPException(status_code=400, detail="사용자 이름은 영어 소문자와 숫자로만 구성되어야 합니다.")

    # 비밀번호 규칙 확인
    password_regex = re.compile(r"""
        (?=.*[a-z])          # 적어도 하나의 소문자
        (?=.*[A-Z])          # 적어도 하나의 대문자
        (?=.*\d)             # 적어도 하나의 숫자
        (?=.*[@$!%*?&\-_+=<>]) # 적어도 하나의 특수문자
        .{10,}               # 길이는 10자 이상
    """, re.VERBOSE)

    if not password_regex.match(signup_data.password):
        raise HTTPException(status_code=400, detail="비밀번호는 최소 10자 이상이며, 대문자, 소문자, 숫자 및 특수문자가 포함되어야 합니다.")
    # username 중복 확인
    existing_user = db.query(User).filter(User.username == signup_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자 이름 입니다.")
    hashed_password = get_password_hash(signup_data.password) # 비밀번호 해시 기능
    new_user = User(username=signup_data.username, email=signup_data.email, hashed_password=hashed_password)
    db.add(new_user)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback() # 에러 발생 시 롤백
        raise HTTPException(status_code=500, detail="회원 가입 실패. 다시 시도해 주세요.")
    db.refresh(new_user)
    return {"message": "회원가입을 성공하였습니다."}

# 로그인
@router.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session=Depends(get_db)):
    user = db.query(User).filter(User.username == signin_data.username).first()
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "로그인 성공!"}
    else:
        raise HTTPException(status_code=401, detail="로그인이 실패하였습니다.")

# 로그아웃
@router.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 완료!"}


# 메모 생성
@router.post("/memos")
async def create_user(request: Request, memo: MemoCreate, db:Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다.")
    new_memo = Memo(user_id=user.id, title = memo.title, content = memo.content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)
    # 새로 생성된 사용자 정보 반환
    return new_memo

# 메모 조회
@router.get("/memos")
async def list_memos(request: Request, db: Session = Depends(get_db)):
    # 사용자별 메모 관리
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다.")
    memos = db.query(Memo).filter(Memo.user_id == user.id).all()
    # 리스트 내포 사용하여 전체 정보 반환
    return templates.TemplateResponse("memos.html", {
        "request": request, 
        "memos": memos,
        "username": username}) # 사용자 이름 추가

# 메모 수정
@router.put("/memos/{memo_id}")
async def update_user(request:Request, memo_id: int, memo: MemoUpdate, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다.")
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    if db_memo is None:
        return {"error": "User를 찾을 수 없습니다."}
    
    # 사용자 정보 업데이트
    if memo.title is not None:
        db_memo.title = memo.title
    if memo.content is not None:
        db_memo.content = memo.content

    db.commit()
    db.refresh(db_memo)
    return db_memo

# 메모 삭제
@router.delete("/memos/{memo_id}")
async def delete_user(request:Request, memo_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다.")
    db_memo = db.query(Memo).filter(Memo.id == memo_id, Memo.user_id == user.id).first()
    if db_memo is None:
        return {"error": "Memo를 찾을 수 없습니다."}
    db.delete(db_memo)
    db.commit()
    return {"message": "Memo가 삭제되었습니다."}

# 라우트
@router.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})

# 'About' 페이지 추가
@router.get('/about')
async def about():
    return {"message": "메모 앱 소개 페이지 입니다."}

# 구글 로그인 후 사용자 정보 처리
def create_or_update_user(db: Session, user_info: dict):
    user = db.query(User).filter(
        (User.email == user_info['email']) | (User.google_id == user_info['google_id'])
    ).first()

    if not user:
        # 신규 사용자 생성
        user = User(
            username=user_info.get('username'),
            email=user_info['email'],
            google_id=user_info['google_id']
        )
        db.add(user)
    else:
        # 기존 사용자 정보 업데이트
        user.username = user_info.get('username') or user.username  # 이름이 없으면 업데이트 하지 않음
        user.google_id = user_info['google_id']  # 구글 ID는 업데이트
        db.merge(user)  # 업데이트 후 세션에 반영

    db.commit()
    db.refresh(user)
    return user