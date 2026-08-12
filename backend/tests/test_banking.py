"""Focused pytest suite covering the required banking behaviors:
deposits, withdrawals, transfers, idempotency, and replication."""

from backend.generated import banking_pb2
from .conftest import balance_of


def test_deposit_updates_balance(branch):
    service, session_factory = branch
    resp = service.Deposit(
        banking_pb2.DepositRequest(account_id=1, amount=10_000, transaction_id="tx-deposit"), None
    )
    assert resp.status == "SUCCESS"
    assert balance_of(session_factory, 1) == 110_000  # seeded 100_000 + 10_000


def test_withdraw_fails_for_insufficient_funds(branch):
    service, session_factory = branch
    resp = service.Withdraw(
        banking_pb2.WithdrawRequest(account_id=3, amount=99_999_999, transaction_id="tx-withdraw"), None
    )
    assert resp.status == "FAILED"
    assert balance_of(session_factory, 3) == 50_000  # unchanged


def test_transfer_debits_and_credits(branch):
    service, session_factory = branch
    resp = service.Transfer(
        banking_pb2.TransferRequest(from_account=1, to_account=2, amount=10_000, transaction_id="tx-transfer"), None
    )
    assert resp.status == "SUCCESS"
    assert balance_of(session_factory, 1) == 90_000
    assert balance_of(session_factory, 2) == 210_000


def test_duplicate_transaction_id_executes_only_once(branch):
    service, session_factory = branch
    request = banking_pb2.DepositRequest(account_id=1, amount=10_000, transaction_id="tx-dup")

    first = service.Deposit(request, None)
    second = service.Deposit(request, None)

    assert first.status == "SUCCESS"
    assert "Duplicate" in second.message
    assert balance_of(session_factory, 1) == 110_000  # applied exactly once


def test_replication_updates_another_branch(two_branches):
    service1, _service2, _sf1, sf2 = two_branches

    resp = service1.Deposit(
        banking_pb2.DepositRequest(account_id=1, amount=10_000, transaction_id="tx-replicate"), None
    )

    assert resp.status == "SUCCESS"
    assert 2 in resp.replicated_to
    assert balance_of(sf2, 1) == 110_000  # Branch 2 picked up the same deposit


def test_duplicate_replication_does_not_apply_twice(branch):
    service, session_factory = branch
    replicate_request = banking_pb2.ReplicateRequest(
        transaction_id="tx-replicate-dup", type="DEPOSIT",
        from_account=0, to_account=1, amount=5_000, status="SUCCESS", origin_branch=1,
    )

    first = service.ReplicateTransaction(replicate_request, None)
    second = service.ReplicateTransaction(replicate_request, None)

    assert first.applied is True
    assert second.applied is False
    assert balance_of(session_factory, 1) == 105_000  # applied exactly once
