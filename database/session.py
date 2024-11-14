from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# MySQL 연결 URL을 환경 변수에서 불러오기
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,           # 연결 풀의 크기 (필요에 따라 조정 가능)
    max_overflow=20,        # 풀 초과 연결 개수
    pool_timeout=30,        # 풀에서 연결을 가져오는 데 걸리는 최대 시간(초)
    pool_recycle=1800,      # 연결이 재활용되기 전에 살아 있을 수 있는 최대 시간(초)
)
# 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 생성 (모든 SQLAlchemy 모델이 상속받을 클래스)
Base = declarative_base()

# Dependency - 데이터베이스 세션을 생성하고 반환하는 함수
def get_db():
    db = SessionLocal()
    try :
        yield db
    finally :
        db.close()