from functools import lru_cache

from sympy import *


@lru_cache(maxsize=None)
def get_minimal_polynomial(expr, t):
    return minimal_polynomial(expr, t)


def are_expressions_approx_equal(expr1, expr2, tol=1e-20):
    val1 = N(expr1, 1000)
    val2 = N(expr2, 1000)
    return abs(val1 - val2) < tol


def fully_simplify(expr):
    expr = expand(expr)
    expr = cancel(expr)
    expr = factor(expr)
    expr = simplify(expr)
    expr = nsimplify(expr, rational=True)
    expr = sqrtdenest(expr)
    expr = ratsimp(expr)
    expr = trigsimp(expr)
    return expr


def my_simplify(expr):
    if expr.is_rational:
        return expr
    expr = sqrtdenest(radsimp(expr))
    t = symbols("t", real=True)
    poly = get_minimal_polynomial(expr, t)
    poly_obj = Poly(poly, t)
    if poly_obj.degree() == 1:
        return -poly_obj.coeff_monomial(1) / poly_obj.coeff_monomial(t)
    elif poly_obj.degree() == 2:
        # Handle quadratic case: a*t^2 + b*t + c = 0
        a, b, c = poly_obj.all_coeffs()  # Returns [a, b, c]

        # Use quadratic formula to compute roots directly
        discriminant = b**2 - 4 * a * c
        if discriminant >= 0:  # Real roots
            root1 = (-b + sqrt(discriminant)) / (2 * a)
            root2 = (-b - sqrt(discriminant)) / (2 * a)

            return root1 if are_expressions_approx_equal(root1, expr) else root2

    roots = solve(poly_obj, t, radicals=True)
    for r in roots:
        if are_expressions_approx_equal(r, expr):
            return r
