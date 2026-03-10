from sympy import sqrt, Pow, simplify
from .sympy_utils import are_expressions_approx_equal, my_simplify
from .point import Point
from .line import Line
from .viewer import viewer, enable_graphics

class Circle:
    def __init__(self, center, other_point):
        # center.simplify()
        # other_point.simplify()
        if center.isEqual(other_point):
            raise ValueError("Circle must pass through a point different than it's origin")
        self.center = center
        self.other_point = other_point
        self.radius = Point.dist(center, other_point)
        if enable_graphics:
            viewer.add_circle(center.x, center.y, self.radius)
    
    @staticmethod
    def get_circle(center, radius):
        return Circle(center, Point(center.x - radius, center.y))
    
    @staticmethod
    def get_intersection(c1, c2):
        A = 2 * (c1.center.x - c2.center.x)
        B = 2 * (c1.center.y - c2.center.y)
        C = -(c1.center.x**2
            + c1.center.y**2
            - c1.radius**2
            - c2.center.x**2
            - c2.center.y**2
            + c2.radius**2)
        return c1.intersect_with_line(Line.get_line_using_ABC(A,B,C))

    def intersect(self, c):
        return Circle.get_intersection(self, c)

    def intersect_with_line(self, l):
        ret = []
        d = l.dist_from_point(self.center)
        if d < self.radius:
            # In this case, there will be two intersection points
            if l.A == 0:
                y = -l.C/l.B
                xs = sqrt(self.radius**2 - (y - self.center.y)**2)
                ret.extend([Point(self.center.x + xs, y), Point(self.center.x - xs, y)])
            elif l.B == 0:
                x = -l.C/l.A
                ys = sqrt(self.radius**2 - (x - self.center.x)**2)
                ret.extend([Point(x, self.center.y + ys), Point(x, self.center.y - ys)])
            else:
                x1 = (-sqrt(-self.center.x**2*l.slope**2 + 2*self.center.y*(self.center.x*l.slope + l.intercept) - 2*self.center.x*l.intercept*l.slope - self.center.y**2 - l.intercept**2 + (l.slope*self.radius)**2 + self.radius**2) + self.center.x + self.center.y*l.slope - l.intercept*l.slope)/(l.slope**2 + 1)
                x2 = (sqrt(-self.center.x**2*l.slope**2 + 2*self.center.y*(self.center.x*l.slope + l.intercept) - 2*self.center.x*l.intercept*l.slope - self.center.y**2 - l.intercept**2 + (l.slope*self.radius)**2 + self.radius**2) + self.center.x + self.center.y*l.slope - l.intercept*l.slope)/(l.slope**2 + 1)
                ret.extend([l.at(x1), l.at(x2)])
        elif simplify(d - self.radius) == 0: 
            # In this case, there will be one intersection point
            if l.A == 0:
                y = -l.C/l.B
                ret.append(Point(self.center.x, y))
            elif l.B == 0:
                x = -l.C/l.A
                ret.append(Point(x, self.center.y))
            else:
                x = (-sqrt(-self.center.x**2*l.slope**2 + 2*self.center.y*(self.center.x*l.slope + l.intercept) - 2*self.center.x*l.intercept*l.slope - self.center.y**2 - l.intercept**2 + (l.slope*self.radius)**2 + self.radius**2) + self.center.x + self.center.y*l.slope - l.intercept*l.slope)/(l.slope**2 + 1)
                ret.append(l.at(x))
        # for i in ret:
        #    i.simplify()
        return ret
    
    def isEqual(self, other):
        return self.center.isEqual(other.center) and self.radius == other.radius

    def __eq__(self, other):
        return self.center.isEqual(other.center) and self.radius == other.radius
    
    def __hash__(self):
        return hash((self.center, self.radius))

    def __str__(self):
        s = ""
        if self.center.x != 0:
            s += "(x - (" + str(self.center.x) + "))^2 + "
        else:
            s += "x^2 + "
        if self.center.y != 0:
            s += "(y - (" + str(self.center.y) + "))^2 = "
        else:
            s += "y^2 = "
        return s + str(self.radius**2)
