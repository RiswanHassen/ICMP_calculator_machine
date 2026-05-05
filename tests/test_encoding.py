import pytest

from core.encoding import AtomicOp, decode, decompose, dispatch, expected


class TestDecompose:
    def test_add_yields_two_operands(self):
        assert decompose("add", 5, 3) == [5, 3]

    def test_sub_yields_two_operands(self):
        assert decompose("sub", 5, 3) == [5, 3]

    def test_mul_yields_b_copies_of_a(self):
        assert decompose("mul", 5, 3) == [5, 5, 5]

    def test_mul_with_zero_b_is_empty(self):
        assert decompose("mul", 5, 0) == []

    def test_mul_with_zero_a_is_zeros(self):
        assert decompose("mul", 0, 3) == [0, 0, 0]

    def test_unsupported_raises(self):
        with pytest.raises(ValueError, match="unsupported operation"):
            decompose("div", 5, 3)


class TestExpected:
    @pytest.mark.parametrize(
        "op, a, b, want",
        [
            ("add", 5, 3, 8),
            ("sub", 5, 3, 2),
            ("sub", 2, 5, -3),  # negative result preserved (no clamping)
            ("mul", 4, 3, 12),
            ("mul", 0, 3, 0),
            ("mul", 4, 0, 0),
        ],
    )
    def test_expected(self, op, a, b, want):
        assert expected(op, a, b) == want

    def test_unsupported_raises(self):
        with pytest.raises(ValueError):
            expected("div", 5, 3)


class TestDispatch:
    def test_round_robin_assignment(self):
        ops = dispatch("add", 5, 3, ["a", "b"], [100, 200])
        assert [(o.op_idx, o.count, o.host, o.icmp_id) for o in ops] == [
            (0, 5, "a", 100),
            (1, 3, "b", 200),
        ]

    def test_modulo_wrap_when_more_ops_than_targets(self):
        # mul(4, 3) → 3 ops, 2 targets → hosts cycle a,b,a
        ops = dispatch("mul", 4, 3, ["a", "b"], [1, 2, 3])
        assert [o.host for o in ops] == ["a", "b", "a"]
        assert [o.count for o in ops] == [4, 4, 4]

    def test_returns_atomicop_instances(self):
        ops = dispatch("add", 1, 2, ["h"], [42, 43])
        assert all(isinstance(o, AtomicOp) for o in ops)

    def test_empty_targets_raises(self):
        with pytest.raises(ValueError, match="at least one target"):
            dispatch("add", 1, 2, [], [10, 20])

    def test_id_pool_too_small_raises(self):
        with pytest.raises(ValueError, match="id pool"):
            dispatch("mul", 5, 3, ["a"], [1, 2])  # 3 ops, 2 ids

    def test_id_pool_larger_than_needed_is_ok(self):
        ops = dispatch("add", 1, 2, ["a"], [10, 20, 30, 40])
        assert [o.icmp_id for o in ops] == [10, 20]


class TestDecode:
    def test_add_sums_replies(self):
        assert decode("add", [5, 3]) == 8

    def test_sub_is_first_minus_second(self):
        assert decode("sub", [5, 3]) == 2

    def test_sub_can_be_negative(self):
        assert decode("sub", [2, 5]) == -3

    def test_sub_with_wrong_op_count_raises(self):
        with pytest.raises(ValueError, match="exactly 2"):
            decode("sub", [1, 2, 3])

    def test_mul_sums_replies(self):
        assert decode("mul", [5, 5, 5]) == 15

    def test_mul_empty_is_zero(self):
        assert decode("mul", []) == 0

    def test_unsupported_raises(self):
        with pytest.raises(ValueError):
            decode("div", [1, 2])


class TestRoundTrip:
    """decode(decompose(...)) == expected(...) — the core invariant."""

    @pytest.mark.parametrize(
        "op, a, b",
        [
            ("add", 5, 3),
            ("add", 0, 0),
            ("sub", 7, 2),
            ("sub", 2, 7),
            ("mul", 4, 3),
            ("mul", 0, 5),
            ("mul", 5, 0),
        ],
    )
    def test_decode_of_decompose_equals_expected(self, op, a, b):
        assert decode(op, decompose(op, a, b)) == expected(op, a, b)
