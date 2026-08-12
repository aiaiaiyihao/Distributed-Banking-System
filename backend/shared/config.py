"""Shared configuration for branches and the gateway.

All values can be overridden with environment variables so the same
code runs unmodified on a developer machine or inside Docker Compose.
"""

import os

# Branch id -> gRPC port. Every branch listens on 0.0.0.0:<port>.
BRANCH_PORTS = {
    1: 50051,
    2: 50052,
    3: 50053,
}

# Branch id -> hostname other services use to reach it. Defaults to
# localhost for local development; Docker Compose overrides these
# with the service names (branch1, branch2, branch3).
BRANCH_HOSTS = {
    1: os.environ.get("BRANCH_1_HOST", "localhost"),
    2: os.environ.get("BRANCH_2_HOST", "localhost"),
    3: os.environ.get("BRANCH_3_HOST", "localhost"),
}


def branch_address(branch_id: int) -> str:
    return f"{BRANCH_HOSTS[branch_id]}:{BRANCH_PORTS[branch_id]}"


# Every account starts out seeded identically on all three branches,
# so the demo can show replication keeping them in sync.
SEED_ACCOUNTS = {
    1: 100_000,  # $1,000.00
    2: 200_000,  # $2,000.00
    3: 50_000,   # $500.00
}

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))


def database_path(branch_id: int) -> str:
    return os.path.join(DATA_DIR, f"branch{branch_id}.db")


GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", 8000))

TRANSACTION_TYPES = ("DEPOSIT", "WITHDRAW", "TRANSFER")
TRANSACTION_STATUSES = ("SUCCESS", "FAILED")
