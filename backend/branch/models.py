"""SQLAlchemy models for a single Branch's local database."""

from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True)
    balance = Column(BigInteger, nullable=False)  # integer cents
    updated_at = Column(DateTime, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, unique=True)
    type = Column(String, nullable=False)  # DEPOSIT | WITHDRAW | TRANSFER
    from_account = Column(Integer, nullable=True)
    to_account = Column(Integer, nullable=True)
    amount = Column(BigInteger, nullable=False)  # integer cents
    status = Column(String, nullable=False)  # SUCCESS | FAILED
    origin_branch = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
