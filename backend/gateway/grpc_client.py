"""Thin gRPC client wrapper used by the FastAPI gateway.

The gateway never touches a Branch database directly — every read or
write goes through one of these gRPC calls.
"""

import grpc

from backend.generated import banking_pb2, banking_pb2_grpc
from backend.shared.config import BRANCH_PORTS, branch_address

RPC_TIMEOUT_SECONDS = 5.0

_stubs: dict[int, banking_pb2_grpc.BranchServiceStub] = {}


def _stub(branch_id: int) -> banking_pb2_grpc.BranchServiceStub:
    if branch_id not in BRANCH_PORTS:
        raise ValueError(f"Unknown branch_id {branch_id}")
    stub = _stubs.get(branch_id)
    if stub is None:
        channel = grpc.insecure_channel(branch_address(branch_id))
        stub = banking_pb2_grpc.BranchServiceStub(channel)
        _stubs[branch_id] = stub
    return stub


def deposit(branch_id: int, account_id: int, amount: int, transaction_id: str):
    return _stub(branch_id).Deposit(
        banking_pb2.DepositRequest(account_id=account_id, amount=amount, transaction_id=transaction_id),
        timeout=RPC_TIMEOUT_SECONDS,
    )


def withdraw(branch_id: int, account_id: int, amount: int, transaction_id: str):
    return _stub(branch_id).Withdraw(
        banking_pb2.WithdrawRequest(account_id=account_id, amount=amount, transaction_id=transaction_id),
        timeout=RPC_TIMEOUT_SECONDS,
    )


def transfer(branch_id: int, from_account: int, to_account: int, amount: int, transaction_id: str):
    return _stub(branch_id).Transfer(
        banking_pb2.TransferRequest(
            from_account=from_account, to_account=to_account, amount=amount, transaction_id=transaction_id,
        ),
        timeout=RPC_TIMEOUT_SECONDS,
    )


def get_account(branch_id: int, account_id: int):
    return _stub(branch_id).GetAccount(
        banking_pb2.GetAccountRequest(account_id=account_id), timeout=RPC_TIMEOUT_SECONDS,
    )


def get_transactions(branch_id: int, limit: int = 50):
    return _stub(branch_id).GetTransactions(
        banking_pb2.GetTransactionsRequest(limit=limit), timeout=RPC_TIMEOUT_SECONDS,
    )
