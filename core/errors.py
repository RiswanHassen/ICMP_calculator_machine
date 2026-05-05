"""Machine-readable failure modes. The final log line of any run is
either ``RUN_OK`` (code=OK) or ``RUN_FAIL <code>``; downstream tooling
keys off these enum values, not free-text messages."""
from enum import Enum


class ErrorCode(str, Enum):
    OK = "OK"
    NO_TARGETS = "NO_TARGETS"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    RAW_SOCKET_DENIED = "RAW_SOCKET_DENIED"
    SNIFFER_ATTACH_FAILED = "SNIFFER_ATTACH_FAILED"
    RESULT_MISMATCH = "RESULT_MISMATCH"
