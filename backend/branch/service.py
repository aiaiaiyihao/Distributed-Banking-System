"""gRPC servicer implementing the banking operations for one Branch.

Each Branch only ever touches its own local SQLite database. After a
deposit/withdraw/transfer commits locally, the same completed
transaction is replicated synchronously to the other branches via
ReplicateTransaction so their copies stay in sync.
"""

import threading
from datetime import datetime, timezone

import grpc

from backend.generated import banking_pb2, banking_pb2_grpc
from backend.branch.models import Account, Transaction
from backend.shared.config import BRANCH_PORTS, branch_address

REPLICATION_TIMEOUT_SECONDS = 2.0


class BranchService(banking_pb2_grpc.BranchServiceServicer):
    def __init__(self, branch_id: int, session_factory):
        self.branch_id = branch_id
        self.session_factory = session_factory
        # Serializes all writes so concurrent requests can't race on the
        # same SQLite file. Fine for a demo project's request volume.
        self.lock = threading.Lock()
        self.peer_branch_ids = [b for b in BRANCH_PORTS if b != branch_id]
        self._peer_stubs = {}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _stub_for(self, peer_id: int):
        stub = self._peer_stubs.get(peer_id)
        if stub is None:
            channel = grpc.insecure_channel(branch_address(peer_id))
            stub = banking_pb2_grpc.BranchServiceStub(channel)
            self._peer_stubs[peer_id] = stub
        return stub

    @staticmethod
    def _duplicate_response(txn: Transaction) -> banking_pb2.TransactionResponse:
        return banking_pb2.TransactionResponse(
            transaction_id=txn.transaction_id,
            status=txn.status,
            message="Duplicate transaction_id detected. Returning the original result; balance was not changed.",
            replicated_to=[],
            failed_replicas=[],
        )

    @staticmethod
    def _record_transaction(session, **fields) -> Transaction:
        txn = Transaction(created_at=datetime.now(timezone.utc), **fields)
        session.add(txn)
        return txn

    def _replicate(self, *, transaction_id, type_, from_account, to_account, amount, status):
        """Push a completed transaction to every other branch. Best-effort:
        a replica being down does not fail the originating transaction."""
        replicated_to, failed_replicas = [], []
        for peer_id in self.peer_branch_ids:
            try:
                self._stub_for(peer_id).ReplicateTransaction(
                    banking_pb2.ReplicateRequest(
                        transaction_id=transaction_id,
                        type=type_,
                        from_account=from_account or 0,
                        to_account=to_account or 0,
                        amount=amount,
                        status=status,
                        origin_branch=self.branch_id,
                    ),
                    timeout=REPLICATION_TIMEOUT_SECONDS,
                )
                replicated_to.append(peer_id)
            except grpc.RpcError:
                failed_replicas.append(peer_id)
        return replicated_to, failed_replicas

    # ------------------------------------------------------------------
    # client-facing RPCs
    # ------------------------------------------------------------------
    def Deposit(self, request, context):
        with self.lock:
            session = self.session_factory()
            try:
                existing = session.get(Transaction, request.transaction_id)
                if existing:
                    return self._duplicate_response(existing)

                account = session.get(Account, request.account_id)
                if account is None:
                    self._record_transaction(
                        session, transaction_id=request.transaction_id, type="DEPOSIT",
                        from_account=None, to_account=request.account_id, amount=request.amount,
                        status="FAILED", origin_branch=self.branch_id,
                    )
                    session.commit()
                    return banking_pb2.TransactionResponse(
                        transaction_id=request.transaction_id, status="FAILED",
                        message=f"Account {request.account_id} not found.",
                    )

                account.balance += request.amount
                account.updated_at = datetime.now(timezone.utc)
                self._record_transaction(
                    session, transaction_id=request.transaction_id, type="DEPOSIT",
                    from_account=None, to_account=request.account_id, amount=request.amount,
                    status="SUCCESS", origin_branch=self.branch_id,
                )
                session.commit()
            finally:
                session.close()

        replicated_to, failed_replicas = self._replicate(
            transaction_id=request.transaction_id, type_="DEPOSIT",
            from_account=None, to_account=request.account_id, amount=request.amount, status="SUCCESS",
        )
        return banking_pb2.TransactionResponse(
            transaction_id=request.transaction_id, status="SUCCESS", message="Deposit successful.",
            replicated_to=replicated_to, failed_replicas=failed_replicas,
        )

    def Withdraw(self, request, context):
        with self.lock:
            session = self.session_factory()
            try:
                existing = session.get(Transaction, request.transaction_id)
                if existing:
                    return self._duplicate_response(existing)

                account = session.get(Account, request.account_id)
                if account is None or account.balance < request.amount:
                    reason = "not found" if account is None else "insufficient funds"
                    self._record_transaction(
                        session, transaction_id=request.transaction_id, type="WITHDRAW",
                        from_account=request.account_id, to_account=None, amount=request.amount,
                        status="FAILED", origin_branch=self.branch_id,
                    )
                    session.commit()
                    return banking_pb2.TransactionResponse(
                        transaction_id=request.transaction_id, status="FAILED",
                        message=f"Withdrawal rejected: {reason}.",
                    )

                account.balance -= request.amount
                account.updated_at = datetime.now(timezone.utc)
                self._record_transaction(
                    session, transaction_id=request.transaction_id, type="WITHDRAW",
                    from_account=request.account_id, to_account=None, amount=request.amount,
                    status="SUCCESS", origin_branch=self.branch_id,
                )
                session.commit()
            finally:
                session.close()

        replicated_to, failed_replicas = self._replicate(
            transaction_id=request.transaction_id, type_="WITHDRAW",
            from_account=request.account_id, to_account=None, amount=request.amount, status="SUCCESS",
        )
        return banking_pb2.TransactionResponse(
            transaction_id=request.transaction_id, status="SUCCESS", message="Withdrawal successful.",
            replicated_to=replicated_to, failed_replicas=failed_replicas,
        )

    def Transfer(self, request, context):
        with self.lock:
            session = self.session_factory()
            try:
                existing = session.get(Transaction, request.transaction_id)
                if existing:
                    return self._duplicate_response(existing)

                from_acc = session.get(Account, request.from_account)
                to_acc = session.get(Account, request.to_account)

                if from_acc is None or to_acc is None or from_acc.balance < request.amount:
                    reason = "insufficient funds" if from_acc and from_acc.balance < request.amount else "account not found"
                    self._record_transaction(
                        session, transaction_id=request.transaction_id, type="TRANSFER",
                        from_account=request.from_account, to_account=request.to_account, amount=request.amount,
                        status="FAILED", origin_branch=self.branch_id,
                    )
                    session.commit()
                    return banking_pb2.TransactionResponse(
                        transaction_id=request.transaction_id, status="FAILED",
                        message=f"Transfer rejected: {reason}.",
                    )

                # Single local DB transaction: both legs succeed or both fail.
                now = datetime.now(timezone.utc)
                from_acc.balance -= request.amount
                from_acc.updated_at = now
                to_acc.balance += request.amount
                to_acc.updated_at = now
                self._record_transaction(
                    session, transaction_id=request.transaction_id, type="TRANSFER",
                    from_account=request.from_account, to_account=request.to_account, amount=request.amount,
                    status="SUCCESS", origin_branch=self.branch_id,
                )
                session.commit()
            finally:
                session.close()

        replicated_to, failed_replicas = self._replicate(
            transaction_id=request.transaction_id, type_="TRANSFER",
            from_account=request.from_account, to_account=request.to_account,
            amount=request.amount, status="SUCCESS",
        )
        return banking_pb2.TransactionResponse(
            transaction_id=request.transaction_id, status="SUCCESS", message="Transfer successful.",
            replicated_to=replicated_to, failed_replicas=failed_replicas,
        )

    def GetAccount(self, request, context):
        session = self.session_factory()
        try:
            account = session.get(Account, request.account_id)
            if account is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Account {request.account_id} not found.")
                return banking_pb2.AccountResponse()
            return banking_pb2.AccountResponse(
                account_id=account.account_id, balance=account.balance,
                updated_at=account.updated_at.isoformat(),
            )
        finally:
            session.close()

    def GetTransactions(self, request, context):
        session = self.session_factory()
        try:
            limit = request.limit or 50
            rows = (
                session.query(Transaction)
                .order_by(Transaction.created_at.desc())
                .limit(limit)
                .all()
            )
            transactions = [
                banking_pb2.Transaction(
                    transaction_id=r.transaction_id, type=r.type,
                    from_account=r.from_account or 0, to_account=r.to_account or 0,
                    amount=r.amount, status=r.status, origin_branch=r.origin_branch,
                    created_at=r.created_at.isoformat(),
                )
                for r in rows
            ]
            return banking_pb2.TransactionListResponse(transactions=transactions)
        finally:
            session.close()

    # ------------------------------------------------------------------
    # inter-branch RPC — never triggers further replication
    # ------------------------------------------------------------------
    def ReplicateTransaction(self, request, context):
        with self.lock:
            session = self.session_factory()
            try:
                existing = session.get(Transaction, request.transaction_id)
                if existing:
                    return banking_pb2.ReplicateResponse(
                        applied=False,
                        message="Duplicate transaction_id: replication already applied previously.",
                    )

                from_account = request.from_account or None
                to_account = request.to_account or None

                if request.status == "SUCCESS":
                    now = datetime.now(timezone.utc)
                    if request.type == "DEPOSIT":
                        account = session.get(Account, to_account)
                        if account:
                            account.balance += request.amount
                            account.updated_at = now
                    elif request.type == "WITHDRAW":
                        account = session.get(Account, from_account)
                        if account:
                            account.balance -= request.amount
                            account.updated_at = now
                    elif request.type == "TRANSFER":
                        from_acc = session.get(Account, from_account)
                        to_acc = session.get(Account, to_account)
                        if from_acc:
                            from_acc.balance -= request.amount
                            from_acc.updated_at = now
                        if to_acc:
                            to_acc.balance += request.amount
                            to_acc.updated_at = now

                self._record_transaction(
                    session, transaction_id=request.transaction_id, type=request.type,
                    from_account=from_account, to_account=to_account, amount=request.amount,
                    status=request.status, origin_branch=request.origin_branch,
                )
                session.commit()
                return banking_pb2.ReplicateResponse(applied=True, message="Replicated transaction applied.")
            finally:
                session.close()
