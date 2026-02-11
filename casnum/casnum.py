import functools
import time

from .cas import (
    Circle,
    Line,
    Point,
    double_point_on_x_axis,
    generate_n,
    get_midpoint,
    get_parallel_to_line_through_point,
    get_y_axis,
    half_point_on_x_axis,
    mirror_point,
    mirror_point_on_x_axis,
    get_perpendicular_to_line_through_point
)

origin = Point(0, 0)
unit = Point(1, 0)
x_axis = Line(origin, unit)
y_axis = get_y_axis(origin, unit)
ALLOW_CONSTRUCT_CIRCLE_FROM_CENTER_AND_RADIUS = True

class CasNum:
    def __init__(self, p):
        self.p = p

    def isEqual(self, other):
        return self.p.isEqual(other.p)

    def __gt__(self, other):
        return self.p.x > other.p.x

    def __lt__(self, other):
        return other > self

    def __ge__(self, other):
        return self > other or self.isEqual(other)

    def __le__(self, other):
        return other >= self

    def __eq__(self, other):
        return self.p.isEqual(other.p)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.p)

    def get_num(self):
        return self.p.x

    def to_int(self):
        return int(self.p.x)

    def __int__(self):
        return self.to_int()

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def from_num(n):
        if n > 0:
            p = generate_n(n, origin, unit)
        else:
            p = Point(0, 0)
        return CasNum(p)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def copy(a):
        return CasNum(a.p)

    @functools.lru_cache(maxsize=None)
    def __add__(self, other):
        if self == zero:
            return CasNum.copy(other)
        if other == zero:
            return CasNum.copy(self)
        if self == other:
            return CasNum.mul2(self)
        if ALLOW_CONSTRUCT_CIRCLE_FROM_CENTER_AND_RADIUS:
            c = Circle.get_circle(self.p, Point.dist(origin, other.p))
            p1, p2 = c.intersect_with_line(x_axis)
            if other > zero:
                p = p1 if p1.x > p2.x else p2
            else:
                p = p1 if p1.x < p2.x else p2
            return CasNum(p)
        else:
            midpoint = get_midpoint(Line(self.p, other.p))
            if midpoint == origin:
                return CasNum.copy(zero)
            else:
                return CasNum(double_point_on_x_axis(origin, midpoint))

    @functools.lru_cache(maxsize=None)
    def __sub__(self, other):
        if self.isEqual(other):
            return CasNum.copy(zero)
        else:
            return self + (-other)  # This uses CasNum.__neg__()

    @functools.lru_cache(maxsize=None)
    def __neg__(self):
        return CasNum(mirror_point_on_x_axis(self.p, origin))

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def abs(a):
        if a < zero:
            return -a
        return a

    @functools.lru_cache(maxsize=None)
    def __mod__(self, other):
        """
        Will return self result with the same signedness as the modulos
        """
        if other.isEqual(zero):
            raise ValueError("Cannot taking modulo by zero")
        remainder = CasNum.copy(self)
        abs_b = CasNum.abs(other)

        while CasNum.abs(remainder) >= abs_b:
            to_rem = CasNum.double_until_gt(CasNum.abs(remainder), abs_b)
            if remainder > zero:
                remainder = remainder - to_rem
            else:
                remainder = remainder + to_rem
        if other < zero and remainder > zero:
            remainder = remainder - abs_b
        elif other > zero and remainder < zero:
            remainder = remainder + abs_b
        return remainder

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def double_until_gt(a, b, strict=True):
        to_rem = CasNum.copy(b)
        while a > to_rem or (not strict and a == to_rem):
            to_rem = CasNum.mul2(to_rem)
        return to_rem

    @functools.lru_cache(maxsize=None)
    def __pow__(self, other):
        if other < zero:
            raise ValueError("Power must be non-negative")
        if CasNum.floor(other) != other:
            raise ValueError("Current implementation requires other to be an integer")
        if other == zero:
            return one
        cpy_a = CasNum.copy(self)
        cpy_b = other - one
        while cpy_b > zero:
            cpy_a = cpy_a * self
            cpy_b = cpy_b - one
        return cpy_a

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def pow_mod(a, b, n):
        """
        Using square and multiply
        """
        result = one
        base = a
        b_cpy = CasNum.copy(b)
        two = one + one
        while b_cpy > zero:
            if (b_cpy % two).isEqual(one):
                result = result * base
                if result > n:
                    result = result % n
            base = base * base
            if base > n:
                base = base % n
            b_cpy = b_cpy >> 1

        return result

    @functools.lru_cache(maxsize=None)
    def __floordiv__(self, other):
        """
        This division conforms to python's division, (as opposed to C's round-towards-zero).
        I decided on this since it works nicely with modulo.
        """
        temp = self % other
        temp = self - temp
        return temp / other

    @functools.lru_cache(maxsize=None)
    def __truediv__(self, other):
        if other.isEqual(zero):
            raise ValueError("Cannot divide by zero")
        CasNum.total_time = 0
        # First, take care of signedness
        a_cpy = CasNum.copy(self)
        b_cpy = CasNum.copy(other)
        if a_cpy < zero:
            a_cpy = -a_cpy
        if b_cpy < zero:
            b_cpy = -b_cpy

        # Take care of zero
        if a_cpy == zero:
            return CasNum.copy(zero)
        if b_cpy == zero:
            return CasNum.copy(zero)

        # Now, the actual division algorithm
        neg_unit = mirror_point_on_x_axis(unit, origin)
        c = Circle(origin, a_cpy.p)
        p1, p2 = c.intersect_with_line(y_axis)
        p = p1 if p1.y > p2.y else p2
        l = get_parallel_to_line_through_point(neg_unit, Line(p, b_cpy.p))
        # t1 = time.time()
        p_div = y_axis.intersect(l)
        # t = (time.time() - t1)
        # print(t)
        # CasNum.total_time += t
        p1, p2 = Circle(origin, p_div).intersect_with_line(x_axis)
        ret = CasNum(p1) if p1.x > 0 else CasNum(p2)

        # Finish taking care of signedness
        if self < zero:
            ret = -ret
        if other < zero:
            ret = -ret
        return ret

    @functools.lru_cache(maxsize=None)
    def __mul__(self, other):
        if other.isEqual(one):
            return self
        if self.isEqual(one):
            return other
        # First, take care of signedness
        a_cpy = CasNum.copy(self)
        b_cpy = CasNum.copy(other)
        if a_cpy < zero:
            a_cpy = -a_cpy
        if b_cpy < zero:
            b_cpy = -b_cpy

        # Take care of zero
        if a_cpy.isEqual(zero):
            return CasNum.copy(zero)
        if b_cpy.isEqual(zero):
            return CasNum.copy(zero)

        # Now, actual algorithm
        neg_unit = mirror_point(unit, y_axis)
        c = Circle(origin, a_cpy.p)
        p1, p2 = c.intersect_with_line(y_axis)
        p = p1 if p1.y > p2.y else p2  # positive self, shifted to the y-axis
        l = get_parallel_to_line_through_point(b_cpy.p, Line(p, neg_unit))
        p_mul = y_axis.intersect(l)
        p1, p2 = Circle(origin, p_mul).intersect_with_line(x_axis)
        ret = CasNum(p1) if p1.x > 0 else CasNum(p2)

        # Finish taking care of signedness
        if self < zero:
            ret = -ret
        if other < zero:
            ret = -ret
        return ret

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def mul2(a):
        return CasNum(double_point_on_x_axis(origin, a.p))

    @functools.lru_cache(maxsize=None)
    def __rshift__(self, i):
        """
        Assumes that self is an integer (i.e., cas integer)
        """
        cpy_a = CasNum.copy(self)
        two = CasNum.get_n(2)
        for _ in range(i):
            if (cpy_a % two).isEqual(zero):
                cpy_a = CasNum(half_point_on_x_axis(origin, cpy_a.p))
            else:
                cpy_a = cpy_a - one
                cpy_a = CasNum(half_point_on_x_axis(origin, cpy_a.p))
        return cpy_a

    @functools.lru_cache(maxsize=None)
    def __lshift__(self, i):
        """
        Assumes that a is an integer (i.e., cas integer)
        """
        cpy_a = CasNum.copy(self)
        for _ in range(i):
            cpy_a = CasNum.mul2(cpy_a)
        return cpy_a

    # TODO: Think about whether this is cheating (i.e., assuming we get the number in binary)
    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_n(n):
        invert = n < 0
        if invert:
            n = -n
        bin_str = bin(n)[2:]
        ret = CasNum.copy(zero)
        cur = CasNum(unit)
        for b in bin_str[::-1]:
            if b == "1":
                ret = ret + cur
            cur = CasNum.mul2(cur)
        if invert:
            ret = -ret
        return ret

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def gcd(a, b):
        cpy_a = CasNum.copy(a)
        cpy_b = CasNum.copy(b)
        while not cpy_b.isEqual(zero):
            temp = cpy_a % cpy_b
            cpy_a = cpy_b
            cpy_b = temp
        return CasNum.abs(cpy_a)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def inv_mod(i, n):
        d, x1, x2, y1 = zero, one, zero, one
        temp_n = n

        while i > zero:
            temp1 = temp_n // i
            temp2 = temp_n - (temp1 * i)
            temp_n, i = i, temp2

            x = x2 - (temp1 * x1)
            y = d - (temp1 * y1)

            x2, x1 = x1, x
            d, y1 = y1, y

        if temp_n == one:
            return d % n


    def floor(a):
        return a // one

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def xor_positive(a, b):
        if a < zero or b < zero:
            raise ValueError("XOR is defined for non-negative CasNum integers here.")

        result = CasNum.copy(zero)
        power_of_2 = CasNum.copy(one)  # Represents 2^n, starting n=0
        a_temp = CasNum.copy(a)
        b_temp = CasNum.copy(b)
        two = one + one  # CasNum representation of 2

        while a_temp > zero or b_temp > zero:

            bit_a = a_temp % two
            bit_b = b_temp % two

            xor_bit = bit_a + bit_b

            # If the XORed bit is 1, add the current power of 2 to the result
            if xor_bit == one:
                result = result + power_of_2

            a_temp = a_temp >> 1
            b_temp = b_temp >> 1

            power_of_2 = CasNum.mul2(power_of_2)

        return result

    @functools.lru_cache(maxsize=None)
    def __xor__(self, other):
        if self >= zero and other >= zero:
            return CasNum.xor_positive(self, other)
        twos_n_a = CasNum.double_until_gt(CasNum.abs(self), one)
        twos_n_b = CasNum.double_until_gt(CasNum.abs(other), one)
        twos_n = twos_n_a if twos_n_a >= twos_n_b else twos_n_b
        transform = CasNum.copy(zero)
        cpy_a = self
        cpy_b = other
        if self < zero:
            transform = transform + one
            cpy_a = self + twos_n
        if other < zero:
            transform = transform + one
            cpy_b = other + twos_n
        xor_val = CasNum.xor_positive(cpy_a, cpy_b)
        if transform == one:
            return xor_val - twos_n
        return xor_val

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def and_positive(a, b):
        if a < zero or b < zero:
            raise ValueError("AND is defined for non-negative CasNum integers here.")

        result = CasNum.copy(zero)
        power_of_2 = CasNum.copy(one)  # Represents 2^n, starting n=0
        a_temp = CasNum.copy(a)
        b_temp = CasNum.copy(b)

        while a_temp > zero or b_temp > zero:

            bit_a = a_temp % two
            bit_b = b_temp % two

            and_bit = bit_a + bit_b

            if and_bit == two:
                result = result + power_of_2

            a_temp = a_temp >> 1
            b_temp = b_temp >> 1

            power_of_2 = CasNum.mul2(power_of_2)

        return result

    def __and__(self, other):
        if self >= zero and other >= zero:
            return CasNum.and_positive(self, other)
        twos_n_a = CasNum.double_until_gt(CasNum.abs(self), one)
        twos_n_b = CasNum.double_until_gt(CasNum.abs(other), one)
        twos_n = twos_n_a if twos_n_a >= twos_n_b else twos_n_b
        transform = CasNum.copy(zero)
        cpy_a = self
        cpy_b = other
        if self < zero:
            transform = transform + one
            cpy_a = self + twos_n
        if other < zero:
            transform = transform + one
            cpy_b = other + twos_n
        and_val = CasNum.and_positive(cpy_a, cpy_b)
        if transform > one:
            return and_val - twos_n
        return and_val

    def get_nth_bit(self, n):
        if self < zero or n < 0:
            raise ValueError(" get_nth_bit is defined for non-negative CasNum and bit.")
        temp = CasNum.copy(self)
        temp = temp >> n
        return temp % two

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def or_positive(a, b):
        if a < zero or b < zero:
            raise ValueError("AND is defined for non-negative CasNum integers here.")

        result = CasNum.copy(zero)
        power_of_2 = CasNum.copy(one)  # Represents 2^n, starting n=0
        a_temp = CasNum.copy(a)
        b_temp = CasNum.copy(b)
        two = one + one  # CasNum representation of 2

        while a_temp > zero or b_temp > zero:

            bit_a = a_temp % two
            bit_b = b_temp % two

            or_bit = bit_a + bit_b

            # If the XORed bit is 1, add the current power of 2 to the result
            if or_bit >= one:
                result = result + power_of_2

            a_temp = a_temp >> 1
            b_temp = b_temp >> 1

            power_of_2 = CasNum.mul2(power_of_2)

        return result

    def __or__(self, other):
        if self >= zero and other >= zero:
            return CasNum.or_positive(self, other)
        twos_n_a = CasNum.double_until_gt(CasNum.abs(self), one)
        twos_n_b = CasNum.double_until_gt(CasNum.abs(other), one)
        twos_n = twos_n_a if twos_n_a >= twos_n_b else twos_n_b
        transform = CasNum.copy(zero)
        cpy_a = self
        cpy_b = other
        if self < zero:
            transform = transform + one
            cpy_a = self + twos_n
        if other < zero:
            transform = transform + one
            cpy_b = other + twos_n
        or_val = CasNum.or_positive(cpy_a, cpy_b)
        if transform >= one:
            return or_val - twos_n
        return or_val

    def sqrt(self):
        if self < zero:
            raise ValueError("Only support taking sqrt of non-negative numbers")
        p = (self + one) / two
        q = p - one
        c = Circle(origin, p.p)
        l = get_perpendicular_to_line_through_point(q.p, x_axis)
        p1, p2 = c.intersect_with_line(l)
        p = p1 if p1.y > p2.y else p2
        c = Circle(q.p, p)
        p1, p2 = c.intersect_with_line(x_axis)
        p = p1 if p1.x > p2.x else p2
        return CasNum(p) - q

    def is_prime(self):
        if self == one:
            return False
        if self == two:
            return True
        if self % two == zero:
            return False
        lim = (self.sqrt() + one).floor()
        cur = two + one
        while cur < lim:
            if self % cur == zero:
                return False
            cur = cur + two
        return True

    @staticmethod
    def get_randint_nbits(nbits=32, state=None):
        m = one
        for _ in range(nbits):
            m = CasNum.mul2(m)
        a = CasNum.get_n(1664525)
        c = CasNum.get_n(1013904223)
        if state == None:
            state = CasNum.get_n(int(time.time()*100))
        return (a * state + c) % m

    @staticmethod
    def get_prime(lo, hi, state=None):
        m = one
        for _ in range(32):
            m = CasNum.mul2(m)
        if hi > m:
            raise ValueError("maximal range is currently 2**32")
        a = CasNum.get_n(1664525)
        c = CasNum.get_n(1013904223)
        if state == None:
            state = CasNum.get_n(int(time.time()*100))

        rng = hi - lo + one
        lim = (m / rng).floor() * rng
        cur = lo + state % rng
        while not cur.is_prime():
            state = (a * state + c) % m
            if state >= lim:
                continue
            cur = lo + state % rng
        return cur

    def __str__(self):
        return str(self.p)

zero = CasNum(origin)
one = CasNum(unit)
two = one + one

