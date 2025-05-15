from fastapi import Request, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from models import User, Memo # 모델 import
from schemas import MemoCreate, MemoUpdate # 스키마 import
from dependencies import get_db
from fastapi.templating import Jinja2Templates
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 사용자 조회
def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("id")
    social_id = request.session.get("social_id")
    provider = request.session.get("provider")

    if user_id:
        return db.query(User).filter(User.id == user_id).first()

    if social_id and provider:
        if provider == "google":
            return db.query(User).filter(User.google_id == social_id).first()
        elif provider == "kakao":
            return db.query(User).filter(User.kakao_id == social_id).first()
        elif provider == "naver":
            return db.query(User).filter(User.naver_id == social_id).first()

    return None

# 인증된 사용자
def get_authenticated_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not Authorized")
    return user

# 메모 생성
@router.post("/memos")
async def create_memo(memo: MemoCreate, user: User = Depends(get_authenticated_user), db:Session = Depends(get_db)):
    # 입력 데이터 유효성 검사
    if not memo.title or not memo.content:
        logger.warning("메모 제목 또는 내용이 빈 값입니다.")
        raise HTTPException(status_code=400, detail="Title and content must not be empty")
    
    new_memo = Memo(user_id=user.id, title = memo.title, content = memo.content)
    db.add(new_memo)
    
    try:
        db.commit()
        db.refresh(new_memo)
        logger.info(f"사용자 {user.username}가 새 메모를 생성했습니다: {new_memo.title}")
    except Exception as e:
        logger.error(f"메모 생성 중 오류 발생: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="메모 생성 실패")
    
    # 새로 생성된 사용자 정보 반환
    return new_memo

# 메모 조회
@router.get("/memos")
async def list_memos(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if user is None:
        logger.warning("메모 조회 실패: 인증되지 않은 사용자")
        raise HTTPException(status_code=401, detail="Not Authorized")
    
    memos = db.query(Memo).filter(Memo.user_id == user.id).all()   
    logger.info(f"사용자 {user.username}의 메모를 조회했습니다.")

    # 리스트 내포 사용하여 전체 정보 반환
    return templates.TemplateResponse("memos.html", {
        "request": request, 
        "memos": memos,
        "username": user.username, # 사용자 이름 추가
        "user_info": user # 사용자 정보
        }) 

# 메모 수정
@router.put("/memos/{memo_id}")
async def update_memo(request:Request, memo_id: int, memo: MemoUpdate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if user is None:
        logger.warning("메모 수정 실패: 인증되지 않은 사용자")
        raise HTTPException(status_code=401, detail="Not Authorized")
   
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    if db_memo is None:
        logger.warning(f"메모 수정 실패: 메모 ID {memo_id}를 찾을 수 없습니다.")
        return {"error": "User를 찾을 수 없습니다."}
    
    # 사용자 정보 업데이트
    if memo.title is not None:
        db_memo.title = memo.title
    if memo.content is not None:
        db_memo.content = memo.content

    try:
        db.commit()
        db.refresh(db_memo)
        logger.info(f"사용자 {user.username}가 메모 ID {memo_id}를 수정했습니다.")
    except Exception as e:
        logger.error(f"메모 수정 중 오류 발생: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="메모 수정 실패")
    
    return db_memo

# 메모 삭제
@router.delete("/memos/{memo_id}")
async def delete_memo(request:Request, memo_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if user is None:
        logger.warning("메모 삭제 실패: 인증되지 않은 사용자")
        raise HTTPException(status_code=401, detail="Not Authorized")
    
    db_memo = db.query(Memo).filter(Memo.id == memo_id, Memo.user_id == user.id).first()
    if db_memo is None:
        logger.warning(f"매모 삭제 실패: 메모 ID {memo_id}를 찾을 수 없습니다.")
        return {"error": "Memo를 찾을 수 없습니다."}
    
    db.delete(db_memo)
    
    try:
        db.commit()
        logger.info(f"사용자 {user.username}가 메모 ID {memo_id}를 삭제했습니다.")
    except Exception as e:
        logger.error(f"메모 삭제 중 에러 발생: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="메모 삭제 실패")
    
    return {"message": "Memo가 삭제되었습니다."}