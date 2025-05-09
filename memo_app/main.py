from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import psycopg2
from typing import Optional
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")

# 데이터베이스 URL 설정
# postgresql://user명:비밀번호@host이름/db이름
DATABASE_URL = "postgresql://postgres:1234@localhost/memo_app" # 실무에서는 노출되지 않는 것이 좋음

# SQLAlchemy 설정
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# passlib을 사용한 사용자 인증
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 사용자 모델 정의
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True) # 정수형, PK
    username = Column(String(100), unique=True, index=True) # 중복 불가
    email = Column(String(200))
    hashed_password = Column(String(512))

# 회원 가입 시 데이터 검증
class UserCreate(BaseModel):
    username: str
    email: str
    password : str # 해시 전 패스워드

# 회원 로그인 시 데이터 검증
class UserLogin(BaseModel):
    username: str
    password: str # 해시 전 패스워드

# Memo 모델 정의
class Memo(Base):
    __tablename__ = 'memo'
    id = Column(Integer, primary_key=True, index=True) # 정수형, PK 설정
    user_id = Column(Integer, ForeignKey('users.id')) # 사용자 참조 추가
    title = Column(String(100), nullable=False) # 제목, 문자열, 값이 없는 예외 경우 방지
    content = Column(String(1000), nullable=False) # 내용, 문자열, 값이 없는 예외 경우 방지

    user = relationship("User") # 사용자와의 관계 설정

# pydantic 사용하여 데이터 검증 수행
class MemoCreate(BaseModel):
    title: str
    content: str

# BaseModel 상속받아 메모 수정 정의하는 클래스
class MemoUpdate(BaseModel):
    title: Optional[str] = None # 문자열 타입, None 값 가능
    content: Optional[str] = None # 문자열 타입, None 값 가능

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

# 회원 가입
@app.post("/signup")
async def signup(signup_data: UserCreate, db: Session=Depends(get_db)):
    hashed_password = get_password_hash(signup_data.password) # 비밀번호 해시 기능
    new_user = User(username=signup_data.username, email=signup_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "계정이 성공적으로 생성되었습니다.", "user_id": new_user.id}

# 로그인
@app.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session=Depends(get_db)):
    user = db.query(User).filter(User.username == signin_data.username).first()
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "로그인 성공!"}
    else:
        raise HTTPException(status_code=401, detail="유효하지 않은 정보 입니다.")

# 로그아웃
@app.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 완료!"}


# 메모 생성
@app.post("/memos")
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
    return {"id": new_memo.id, "title": new_memo.title, "content": new_memo.content}

# 메모 조회
@app.get("/memos")
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
    return templates.TemplateResponse("memos.html", {"request": request, "memos": memos})

# 메모 수정
@app.put("/memos/{memo_id}")
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
    return {"id": db_memo.id, "title": db_memo.title, "content": db_memo.content}

# 메모 삭제
@app.delete("/memos/{memo_id}")
async def delete_user(request:Request, memo_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다.")
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    if db_memo is None:
        return {"error": "Memo를 찾을 수 없습니다."}
    db.delete(db_memo)
    db.commit()
    return {"message": "Memo가 삭제되었습니다."}

# 라우트
@app.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})

# 'About' 페이지 추가
@app.get('/about')
async def about():
    return {"message": "메모 앱 소개 페이지 입니다."}