from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 데이터베이스 URL 설정
# postgresql://user명:비밀번호@host이름/db이름
DATABASE_URL = "postgresql://postgres:1234@localhost/memo_app" # 실무에서는 노출되지 않는 것이 좋음

# 엔진 생성성
engine = create_engine(DATABASE_URL)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()