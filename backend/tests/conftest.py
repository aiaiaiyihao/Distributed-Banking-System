import time
from concurrent import futures

import grpc
import pytest

from backend.branch.database import make_session_factory
from backend.branch.models import Account
from backend.branch.service import BranchService
from backend.generated import banking_pb2_grpc
from backend.shared.config import BRANCH_PORTS


def balance_of(session_factory, account_id: int) -> int:
    session = session_factory()
    try:
        return session.get(Account, account_id).balance
    finally:
        session.close()


@pytest.fixture
def branch(tmp_path):
    """A single Branch service with no live peers, for tests that only
    care about local behavior (deposit/withdraw/transfer/idempotency)."""
    session_factory = make_session_factory(1, db_path=str(tmp_path / "branch1.db"))
    service = BranchService(1, session_factory)
    service.peer_branch_ids = []
    return service, session_factory


def _start_branch_server(branch_id: int, db_path: str):
    session_factory = make_session_factory(branch_id, db_path=db_path)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    service = BranchService(branch_id, session_factory)
    banking_pb2_grpc.add_BranchServiceServicer_to_server(service, server)
    server.add_insecure_port(f"127.0.0.1:{BRANCH_PORTS[branch_id]}")
    server.start()
    return server, service, session_factory


@pytest.fixture
def two_branches(tmp_path):
    """Two real Branch gRPC servers (Branch 1 and Branch 2) so replication
    can be exercised over an actual network call."""
    server1, service1, sf1 = _start_branch_server(1, str(tmp_path / "branch1.db"))
    server2, service2, sf2 = _start_branch_server(2, str(tmp_path / "branch2.db"))
    time.sleep(0.2)
    try:
        yield service1, service2, sf1, sf2
    finally:
        server1.stop(None)
        server2.stop(None)
