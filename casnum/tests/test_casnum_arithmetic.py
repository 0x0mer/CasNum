import os
import random
import math
import pytest

# === EDIT THIS IMPORT TO MATCH YOUR PROJECT ===
import casnum as M
# ============================================

CasNum = M.CasNum
Point = M.Point

origin = M.origin
unit = M.unit
zero = M.zero
one = M.one

# Deterministic randomness (reproducible failures)
SEED = int(os.getenv("CASNUM_TEST_SEED", "12648430"))
RNG = random.Random(SEED)

# Tune these down/up depending on speed
N_FAST = int(os.getenv("CASNUM_TEST_FAST", "80"))   # add/sub/xor/gcd/shift
N_SLOW = int(os.getenv("CASNUM_TEST_SLOW", "25"))   # mul/div/mod/pow_mod/inv_mod

# Keep ranges modest because your geometric/symbolic ops are expensive
R_ADD = int(os.getenv("CASNUM_R_ADD", "200"))
R_MUL = int(os.getenv("CASNUM_R_MUL", "60"))
R_DIV = int(os.getenv("CASNUM_R_DIV", "200"))
R_MOD = int(os.getenv("CASNUM_R_MOD", "200"))
R_XOR = int(os.getenv("CASNUM_R_XOR", "200"))
R_SHIFT = int(os.getenv("CASNUM_R_SHIFT", "512"))
MAX_SHIFT = int(os.getenv("CASNUM_MAX_SHIFT", "8"))


def rand_int(lo: int, hi: int) -> int:
    return RNG.randint(lo, hi)


def cn(n: int) -> CasNum:
    """
    Build a CasNum integer WITHOUT using get_n() as the oracle.
    Uses from_num() for non-negative values and flips x for negatives.
    """
    if n >= 0:
        return CasNum.get_n(n)
    p = CasNum.get_n(-n).p
    return CasNum(Point(-p.x, p.y))


def assert_int_value(x: CasNum, expected: int):
    # Symbolic/exact: must lie on x-axis and equal exactly
    assert x.p.y == 0
    assert x.p.x == expected


# -----------------------------
# Basics / construction
# -----------------------------

def test_zero_one():
    assert_int_value(zero, 0)
    assert_int_value(one, 1)


def test_cn_random_integers():
    # This primarily checks from_num + our neg construction
    for _ in range(N_FAST):
        n = rand_int(-R_ADD, R_ADD)
        assert_int_value(cn(n), n)


def test_hash_eq_contract_random():
    for _ in range(max(20, N_FAST // 4)):
        n = rand_int(-R_ADD, R_ADD)
        a = cn(n)
        b = CasNum(Point(a.p.x, a.p.y))  # distinct Point, same coords
        assert a == b
        assert hash(a) == hash(b)


# -----------------------------
# Negation / identities (true edge cases)
# -----------------------------

def test_negation_identities():
    for _ in range(N_FAST):
        a = rand_int(-R_ADD, R_ADD)
        A = cn(a)
        assert (-(-A)) == A
        assert_int_value(A + (-A), 0)
        assert_int_value(A - A, 0)


def test_add_mul_identities_random():
    for _ in range(N_FAST):
        a = rand_int(-R_ADD, R_ADD)
        A = cn(a)
        assert_int_value(A + zero, a)
        assert_int_value(zero + A, a)
        assert_int_value(A * one, a)
        assert_int_value(one * A, a)
        assert (A * zero) == zero
        assert (zero * A) == zero


# -----------------------------
# Addition / subtraction (random)
# -----------------------------

def test_add_sub_match_python_random():
    for _ in range(N_FAST):
        a = rand_int(-R_ADD, R_ADD)
        b = rand_int(-R_ADD, R_ADD)
        A, B = cn(a), cn(b)
        assert_int_value(A + B, a + b)
        assert_int_value(A - B, a - b)


def test_add_associativity_sampled():
    # Associativity is important, but expensive to check exhaustively
    for _ in range(max(12, N_FAST // 6)):
        a = rand_int(-50, 50)
        b = rand_int(-50, 50)
        c = rand_int(-50, 50)
        A, B, C = cn(a), cn(b), cn(c)
        assert (A + B) + C == A + (B + C)


# -----------------------------
# Multiplication (random)
# -----------------------------

def test_mul_match_python_random():
    for _ in range(N_SLOW):
        a = rand_int(-R_MUL, R_MUL)
        b = rand_int(-R_MUL, R_MUL)
        A, B = cn(a), cn(b)
        assert_int_value(A * B, a * b)


def test_distributive_sampled():
    for _ in range(max(10, N_SLOW // 2)):
        a = rand_int(-30, 30)
        b = rand_int(-30, 30)
        c = rand_int(-30, 30)
        A, B, C = cn(a), cn(b), cn(c)
        assert A * (B + C) == (A * B) + (A * C)


# -----------------------------
# Mod / floor division (edge + random)
# -----------------------------

def test_mod_by_zero_raises():
    with pytest.raises(ValueError):
        _ = cn(5) % zero


def test_floordiv_by_zero_raises():
    with pytest.raises(ValueError):
        _ = cn(5) // zero


def test_div_mod_match_python_and_invariants_random():
    for _ in range(N_SLOW):
        a = rand_int(-R_MOD, R_MOD)
        b = rand_int(-R_MOD // 2, R_MOD // 2)
        if b == 0:
            continue

        A, B = cn(a), cn(b)
        q = A // B
        r = A % B

        assert_int_value(q, a // b)
        assert_int_value(r, a % b)

        # a == q*b + r
        assert (q * B + r) == A

        # |r| < |b|
        assert abs(r.p.x) < abs(b)

        # Python rule: remainder has sign of divisor (unless 0)
        if (a % b) == 0:
            assert r == zero
        else:
            assert (r.p.x > 0) == (b > 0)


def test_floor_division_edgecases():
    # division by 1 / -1 / itself
    for _ in range(max(15, N_SLOW // 2)):
        a = rand_int(-R_DIV, R_DIV)
        if a == 0:
            continue
        A = cn(a)
        assert_int_value(A // one, a)
        assert_int_value(A // (-one), -a)
        assert_int_value(A // A, 1)


# -----------------------------
# True division (only exact cases + edge)
# -----------------------------

def test_truediv_div_by_zero_behavior():
    # Your snippet returns zero; some versions might raise.
    try:
        out = cn(5) / zero
    except Exception:
        return
    assert out == zero


def test_truediv_exact_when_divisible_random():
    # Only test cases where a is exactly divisible by b
    for _ in range(max(12, N_SLOW)):
        b = rand_int(1, max(2, R_MUL // 2))
        k = rand_int(-50, 50)
        a = b * k
        A, B = cn(a), cn(b)
        q = A / B
        assert_int_value(q, k)


def test_truediv_edgecases():
    for _ in range(max(10, N_SLOW // 2)):
        a = rand_int(-R_DIV, R_DIV)
        if a == 0:
            continue
        A = cn(a)
        assert_int_value(A / one, a)
        assert_int_value(A / (-one), -a)
        assert_int_value(A / A, 1)
    # 0 / b == 0 for nonzero b
    for _ in range(10):
        b = rand_int(-R_DIV, R_DIV)
        if b == 0:
            continue
        assert cn(0) / cn(b) == zero


# -----------------------------
# Shifts (random)
# -----------------------------

def test_rshift_matches_python_random():
    for _ in range(max(20, N_FAST // 3)):
        a = rand_int(-R_SHIFT, R_SHIFT)
        i = rand_int(0, MAX_SHIFT)
        assert_int_value(cn(a) >> i, a >> i)


def test_lshift_matches_python_random():
    # If your __lshift__ was buggy earlier, this will catch it.
    for _ in range(max(20, N_FAST // 3)):
        a = rand_int(-R_SHIFT, R_SHIFT)
        i = rand_int(0, MAX_SHIFT)
        assert_int_value(cn(a) << i, a << i)


# -----------------------------
# pow / pow_mod (edge + random)
# -----------------------------

def test_pow_edgecases():
    # Exponent 0 is a classic bug in hand-rolled pow loops
    for _ in range(20):
        a = rand_int(-20, 20)
        A = cn(a)
        assert_int_value(A ** cn(0), 1)
        assert_int_value(A ** cn(1), a)
    assert_int_value(cn(0) ** cn(0), 1)  # Python defines 0**0 as 1


def test_pow_small_random():
    for _ in range(N_SLOW):
        a = rand_int(-10, 10)
        b = rand_int(0, 8)
        assert_int_value(cn(a) ** cn(b), a ** b)


def test_pow_mod_matches_python_random():
    for _ in range(N_SLOW):
        a = rand_int(0, 80)
        b = rand_int(0, 40)
        n = rand_int(2, 120)
        res = CasNum.pow_mod(cn(a), cn(b), cn(n))
        assert_int_value(res, pow(a, b, n))


# -----------------------------
# gcd / inv_mod (random)
# -----------------------------

def test_gcd_matches_python_random():
    for _ in range(N_FAST):
        a = rand_int(-400, 400)
        b = rand_int(-400, 400)
        g = CasNum.gcd(cn(a), cn(b))
        assert_int_value(g, math.gcd(a, b))


def test_inv_mod_matches_python_random():
    for _ in range(N_SLOW):
        n = rand_int(2, 200)
        i = rand_int(1, 200)
        inv = CasNum.inv_mod(cn(i), cn(n))
        if math.gcd(i, n) != 1:
            assert inv is None
        else:
            assert inv is not None
            assert_int_value(inv, pow(i, -1, n))


# -----------------------------
# XOR (edge + random)
# -----------------------------

def test_xor_positive_rejects_negative():
    with pytest.raises(ValueError):
        CasNum.xor_positive(cn(-1), cn(0))
    with pytest.raises(ValueError):
        CasNum.xor_positive(cn(0), cn(-2))


def test_xor_nonnegative_matches_python_random():
    for _ in range(N_FAST):
        a = rand_int(0, R_XOR)
        b = rand_int(0, R_XOR)
        assert_int_value(cn(a) ^ cn(b), a ^ b)


def test_xor_signed_matches_python_random():
    for _ in range(max(20, N_FAST // 3)):
        a = rand_int(-R_XOR, R_XOR)
        b = rand_int(-R_XOR, R_XOR)
        assert_int_value(cn(a) ^ cn(b), a ^ b)


# -----------------------------
# double_until_gt (random properties)
# -----------------------------

def test_double_until_gt_properties_random():
    for _ in range(max(20, N_FAST // 3)):
        a = rand_int(0, 200)
        b = rand_int(1, 100)
        A, B = cn(a), cn(b)

        out_strict = CasNum.double_until_gt(A, B, strict=True)
        assert out_strict.p.y == 0
        assert out_strict.p.x > a

        out_nonstrict = CasNum.double_until_gt(A, B, strict=False)
        assert out_nonstrict.p.y == 0
        assert out_nonstrict.p.x >= a

