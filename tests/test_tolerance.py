from decimal import Decimal

from parity.checks import within


def test_float_noise_fails_exact_without_scale():
    # 0.1 + 0.2 is 0.30000000000000004 as a float
    assert not within(0.1 + 0.2, Decimal("0.3"), "exact")


def test_float_noise_passes_exact_with_scale():
    assert within(254199.72999999998, Decimal("254199.73"), "exact", scale=2)


def test_one_cent_off_fails_exact():
    assert not within(Decimal("100.00"), Decimal("100.01"), "exact", scale=2)


def test_relative_tolerance_boundary():
    assert within(1000, 1001, 0.001)          # exactly 0.1%: allowed
    assert not within(1000, 1002, 0.001)      # 0.2%: not allowed


def test_zero_source_does_not_divide_by_zero():
    assert within(0, 0, 0.001)
    assert not within(0, 5, 0.001)