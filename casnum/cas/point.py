from sympy import sympify, sqrt, sqrtdenest, radsimp 
from .sympy_utils import my_simplify
from .viewer import viewer, enable_graphics

class Point:
    def __init__(self, x, y):
        self.x = sqrtdenest(radsimp(sympify(x)))
        self.y = sqrtdenest(radsimp(sympify(y)))
        if enable_graphics:
            viewer.add_point(x, y)

    # def simplify(self):
    #     self.x = my_simplify(self.x)
    #     self.y = my_simplify(self.y)
    
    def isEqual(self, p):
            return self.x == p.x and self.y == p.y
    
    def __eq__(self, p):
            return self.x == p.x and self.y == p.y

    def __hash__(self):
        return hash((self.x, self.y))

    @staticmethod
    def is_at_inf(p):
        return p.x.is_infinite or p.y.is_infinite

    @staticmethod
    def dist(p1, p2):
        return sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def size(self):
        return Point.dist(self, Point(0,0))
    
    def __str__(self):
        if self.x.is_algebraic and self.y.is_algebraic:
            return "(" + str(my_simplify(self.x)) + ", " + str(my_simplify(self.y)) + ")"
        else:
            return "(" + str(self.x) + ", " + str(self.y) + ")"


