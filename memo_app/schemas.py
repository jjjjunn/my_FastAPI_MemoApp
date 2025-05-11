from pydantic import BaseModel
from typing import Optional

# 회원 가입 시 데이터 검증
class UserCreate(BaseModel):
    username: str
    email: str
    password : str # 해시 전 패스워드

# 회원 로그인 시 데이터 검증
class UserLogin(BaseModel):
    username: str
    password: str # 해시 전 패스워드

# pydantic 사용하여 데이터 검증 수행
class MemoCreate(BaseModel):
    title: str
    content: str

# BaseModel 상속받아 메모 수정 정의하는 클래스
class MemoUpdate(BaseModel):
    title: Optional[str] = None # 문자열 타입, None 값 가능
    content: Optional[str] = None # 문자열 타입, None 값 가능