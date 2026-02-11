from sympy import Abs, Matrix, sqrt, sympify
from .point import Point
from .sympy_utils import my_simplify
from .viewer import viewer, enable_graphics


class Line:
    # Line in the format of Ax + By + C = 0
    def __init__(self, p1, p2):
        # p1.simplify()
        # p2.simplify()
        self.p1 = p1
        self.p2 = p2
        self.A = p1.y - p2.y
        self.B = p2.x - p1.x
        if self.A == 0 and self.B == 0:
            raise ValueError("Line Ax+By+C = 0 must have non-zero A or B")
        self.C = p1.x * p2.y - p2.x * p1.y
        self.slope = Line.get_slope(self)
        self.intercept = Line.get_intercept(self)
        if enable_graphics:
            viewer.add_line(p1.x, p1.y, p2.x, p2.y)

    def at(self, x):
        return Point(x, self.slope * x + self.intercept)

    def get_y(self, x):
        return Point(x, (self.C - self.A * x) / self.B)

    def get_x(self, y):
        return Point((self.C - self.B * y) / self.A, y)

    @staticmethod
    def get_slope(l):
        return sympify((l.p2.y - l.p1.y) / (l.p2.x - l.p1.x))

    @staticmethod
    def get_intercept(l):
        return sympify(l.p1.y - l.slope * l.p1.x)

    @staticmethod
    def isEqual(self, l):
        return self.slope == l.slope and self.intercept == l.intercept
    
    def __eq__(self, l):
        return self.slope == l.slope and self.intercept == l.intercept

    def __hash__(self):
        return hash((self.A, self.B, self.C))

    @staticmethod
    def get_intersection(l1, l2):
        # m = Matrix(2, 2, [l1.A, l1.B, l2.A, l2.B])
        d = l1.A * l2.B - l1.B * l2.A # Determinant
        if d == 0:
            return Point(zoo, zoo)
        else:
            # x, y = m.solve(Matrix(2, 1, [-l1.C, -l2.C]))
            # Writing out the formulas explicitely for efficiency
            x = (d**-1) * (l2.B * (-l1.C) + l1.B * l2.C)
            y = (d**-1) * (l2.A * l1.C - l1.A * l2.C)

        if x.is_rational and y.is_rational:
            return Point(x, y)

        return Point(my_simplify(x), my_simplify(y))

    def intersect(self, l):
        return Line.get_intersection(self, l)

    def dist_from_point(self, p):
        return Abs(self.A * p.x + self.B * p.y + self.C) / sqrt(self.A**2 + self.B**2)

    def __str__(self):
        s = ""
        if self.A != 0:
            s += str(self.A) + "*x"
        if self.B != 0:
            if self.A != 0:
                s += " + "
            s += str(self.B) + "*y"
        if self.C != 0:
            s += " + " + str(self.C)
        return s + " = 0"
