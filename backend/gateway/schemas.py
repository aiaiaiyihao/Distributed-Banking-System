"""Pydantic request/response models for the FastAPI gateway."""

from typing import Optional
from pydantic import BaseModel


class DepositRequest(BaseModel):
    account_id: int
    amount: int
    branch_id: int
    transaction_id: str


class WithdrawRequest(BaseModel):
    account_id: int
    amount: int
    branch_id: int
    transaction_id: str


class TransferRequest(BaseModel):
    from_account: int
    to_account: int
    amount: int
    branch_id: int
    transaction_id: str


class TransactionResult(BaseModel):
    transaction_id: str
    status: str
    message: str
    replicated_to: list[int]
    failed_replicas: list[int]


class AccountBalance(BaseModel):
    account_id: int
    balance: int
    updated_at: str


class TransactionRecord(BaseModel):
    transaction_id: str
    type: str
    from_account: Optional[int]
    to_account: Optional[int]
    amount: int
    status: str
    origin_branch: int
    created_at: str


class BranchInfo(BaseModel):
    branch_id: int
    name: str
