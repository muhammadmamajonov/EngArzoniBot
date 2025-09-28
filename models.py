from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()


class Elon(Base):
    __tablename__ = "elonlar"

    id = Column(Integer, primary_key=True)
    owner_id = Column(BigInteger, nullable=False)
    phone_number = Column(String, nullable=False)
    description = Column(String, nullable=False)
    plate_number = Column(String, unique=True, nullable=False)
    circled_video_id = Column(String, nullable=True)
    description_id = Column(Integer, nullable=True)
    posted = Column(Boolean, default=False)
    sold = Column(Boolean, default=False)
    check_photo = Column(String, nullable=True)
    pay_with_cash = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Elon(id={self.id}, plate_number='{self.plate_number}')>"