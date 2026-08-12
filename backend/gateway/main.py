"""FastAPI gateway: exposes REST endpoints to the React frontend and
talks to Branch servers exclusively over gRPC."""

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.gateway import grpc_client
from backend.gateway.schemas import (
    DepositRequest, WithdrawRequest, TransferRequest,
    TransactionResult, AccountBalance, TransactionRecord, BranchInfo,
)
from backend.shared.config import BRANCH_PORTS, SEED_ACCOUNTS

app = FastAPI(title="Distributed Banking System Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _grpc_call(fn, *args, not_found_message: str | None = None):
    try:
        return fn(*args)
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=not_found_message or exc.details())
        raise HTTPException(status_code=503, detail=f"Branch unavailable: {exc.details()}")


@app.get("/api/branches", response_model=list[BranchInfo])
def list_branches():
    return [BranchInfo(branch_id=b, name=f"Branch {b}") for b in sorted(BRANCH_PORTS)]


@app.get("/api/accounts", response_model=list[AccountBalance])
def list_accounts(branch_id: int):
    accounts = []
    for account_id in sorted(SEED_ACCOUNTS):
        resp = _grpc_call(grpc_client.get_account, branch_id, account_id)
        accounts.append(AccountBalance(account_id=resp.account_id, balance=resp.balance, updated_at=resp.updated_at))
    return accounts


@app.get("/api/accounts/{account_id}", response_model=AccountBalance)
def get_account(account_id: int, branch_id: int):
    resp = _grpc_call(
        grpc_client.get_account, branch_id, account_id,
        not_found_message=f"Account {account_id} not found on branch {branch_id}.",
    )
    return AccountBalance(account_id=resp.account_id, balance=resp.balance, updated_at=resp.updated_at)


@app.get("/api/transactions", response_model=list[TransactionRecord])
def list_transactions(branch_id: int, limit: int = 50):
    resp = _grpc_call(grpc_client.get_transactions, branch_id, limit)
    return [
        TransactionRecord(
            transaction_id=t.transaction_id, type=t.type,
            from_account=t.from_account or None, to_account=t.to_account or None,
            amount=t.amount, status=t.status, origin_branch=t.origin_branch, created_at=t.created_at,
        )
        for t in resp.transactions
    ]


@app.post("/api/deposit", response_model=TransactionResult)
def deposit(req: DepositRequest):
    resp = _grpc_call(grpc_client.deposit, req.branch_id, req.account_id, req.amount, req.transaction_id)
    return TransactionResult(
        transaction_id=resp.transaction_id, status=resp.status, message=resp.message,
        replicated_to=list(resp.replicated_to), failed_replicas=list(resp.failed_replicas),
    )


@app.post("/api/withdraw", response_model=TransactionResult)
def withdraw(req: WithdrawRequest):
    resp = _grpc_call(grpc_client.withdraw, req.branch_id, req.account_id, req.amount, req.transaction_id)
    return TransactionResult(
        transaction_id=resp.transaction_id, status=resp.status, message=resp.message,
        replicated_to=list(resp.replicated_to), failed_replicas=list(resp.failed_replicas),
    )


@app.post("/api/transfer", response_model=TransactionResult)
def transfer(req: TransferRequest):
    resp = _grpc_call(
        grpc_client.transfer, req.branch_id, req.from_account, req.to_account, req.amount, req.transaction_id,
    )
    return TransactionResult(
        transaction_id=resp.transaction_id, status=resp.status, message=resp.message,
        replicated_to=list(resp.replicated_to), failed_replicas=list(resp.failed_replicas),
    )
