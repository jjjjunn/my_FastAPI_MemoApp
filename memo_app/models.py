from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base

# 사용자 모델 정의
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)  # 정수형, PK
    username = Column(String(100), unique=True, index=True, nullable=True)  # 소셜 로그인 시 자동 설정 가능
    email = Column(String(200), unique=True)  # 이메일은 유일해야 함
    hashed_password = Column(String(512), nullable=True)  # 비밀번호는 선택적
    google_id = Column(String(100), unique=True, index=True, nullable=True)  # 구글 계정의 고유 ID
    kakao_id = Column(String(100), unique=True, index=True, nullable=True) # 카카오 계정의 고유 ID
    naver_id = Column(String(100), unique=True, index=True, nullable=True) # 네이버 계정의 고유 ID

# Memo 모델 정의
class Memo(Base):
    __tablename__ = 'memo'
    id = Column(Integer, primary_key=True, index=True)  # 정수형, PK 설정
    user_id = Column(Integer, ForeignKey('users.id'))  # 사용자 참조 추가
    title = Column(String(100), nullable=False)  # 제목
    content = Column(String(1000), nullable=False)  # 내용

    user = relationship("User")  # 사용자와의 관계 설정  