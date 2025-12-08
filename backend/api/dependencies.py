"""
API Dependencies

FastAPI dependency injection components.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings

# Database setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.

    Yields:
        Database session

    Example:
        @app.get("/videos/{video_id}")
        async def get_video(video_id: str, db: Session = Depends(get_db)):
            video = db.query(Video).filter(Video.id == video_id).first()
            return video
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
