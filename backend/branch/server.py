"""Entry point for running a single Branch gRPC server.

Usage:
    python -m backend.branch.server 1
    BRANCH_ID=1 python -m backend.branch.server
"""

import os
import sys
from concurrent import futures

import grpc

from backend.generated import banking_pb2_grpc
from backend.branch.database import make_session_factory
from backend.branch.service import BranchService
from backend.shared.config import BRANCH_PORTS


def serve(branch_id: int) -> None:
    session_factory = make_session_factory(branch_id)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banking_pb2_grpc.add_BranchServiceServicer_to_server(
        BranchService(branch_id, session_factory), server
    )

    port = BRANCH_PORTS[branch_id]
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"Branch {branch_id} listening on 0.0.0.0:{port}")
    server.wait_for_termination()


def _resolve_branch_id() -> int:
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    return int(os.environ.get("BRANCH_ID", "1"))


if __name__ == "__main__":
    serve(_resolve_branch_id())
