"""Internal modules behind the icmp_calc CLI.

Public surface for callers (e.g. a self-healing harness):

    from core.encoding import SUPPORTED, AtomicOp, decompose, dispatch, decode, expected
    from core.targets  import load_targets
    from core.burst    import burst_send
    from core.sniff    import ReplySniffer
    from core.errors   import ErrorCode
    from core.log      import setup, for_run, new_run_id
"""
