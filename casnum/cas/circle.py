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
        # TODO: Take care of the case of containment of one another
        ret = []
        if Point.dist(c1.center, c2.center) < (c1.radius + c2.radius):
            # In this case, there will be two intersection points
            # Thank god for WolframAlpha
            y1 = c1.center.y - (4 * c1.center.x * c1.center.x * c1.center.y - 4 * c1.center.x * c1.center.x * c2.center.y - sqrt(Pow((-4 * c1.center.x * c1.center.x * c1.center.y + 4 * c1.center.x * c1.center.x * c2.center.y + 8 * c1.center.x * c1.center.y * c2.center.x - 8 * c1.center.x * c2.center.x * c2.center.y - 4 * c1.center.y * c1.center.y * c1.center.y + 12 * c1.center.y * c1.center.y * c2.center.y - 4 * c1.center.y * c2.center.x * c2.center.x - 12 * c1.center.y * c2.center.y * c2.center.y - 4 * c1.center.y * c1.radius * c1.radius + 4 * c1.center.y * c2.radius * c2.radius + 4 * c2.center.x * c2.center.x * c2.center.y + 4 * c2.center.y * c2.center.y * c2.center.y + 4 * c2.center.y * c1.radius * c1.radius - 4 * c2.center.y * c2.radius * c2.radius), 2) - 4 * (4 * c1.center.x * c1.center.x - 8 * c1.center.x * c2.center.x + 4 * c1.center.y * c1.center.y - 8 * c1.center.y * c2.center.y + 4 * c2.center.x * c2.center.x + 4 * c2.center.y * c2.center.y) * (c1.center.x * c1.center.x * c1.center.x * c1.center.x - 4 * c1.center.x * c1.center.x * c1.center.x * c2.center.x + 2 * c1.center.x * c1.center.x * c1.center.y * c1.center.y - 4 * c1.center.x * c1.center.x * c1.center.y * c2.center.y + 6 * c1.center.x * c1.center.x * c2.center.x * c2.center.x + 2 * c1.center.x * c1.center.x * c2.center.y * c2.center.y - 2 * c1.center.x * c1.center.x * c1.radius * c1.radius - 2 * c1.center.x * c1.center.x * c2.radius * c2.radius - 4 * c1.center.x * c1.center.y * c1.center.y * c2.center.x + 8 * c1.center.x * c1.center.y * c2.center.x * c2.center.y - 4 * c1.center.x * c2.center.x * c2.center.x * c2.center.x - 4 * c1.center.x * c2.center.x * c2.center.y * c2.center.y + 4 * c1.center.x * c2.center.x * c1.radius * c1.radius + 4 * c1.center.x * c2.center.x * c2.radius * c2.radius + c1.center.y * c1.center.y * c1.center.y * c1.center.y - 4 * c1.center.y * c1.center.y * c1.center.y * c2.center.y + 2 * c1.center.y * c1.center.y * c2.center.x * c2.center.x + 6 * c1.center.y * c1.center.y * c2.center.y * c2.center.y + 2 * c1.center.y * c1.center.y * c1.radius * c1.radius - 2 * c1.center.y * c1.center.y * c2.radius * c2.radius - 4 * c1.center.y * c2.center.x * c2.center.x * c2.center.y - 4 * c1.center.y * c2.center.y * c2.center.y * c2.center.y - 4 * c1.center.y * c2.center.y * c1.radius * c1.radius + 4 * c1.center.y * c2.center.y * c2.radius * c2.radius + c2.center.x * c2.center.x * c2.center.x * c2.center.x + 2 * c2.center.x * c2.center.x * c2.center.y * c2.center.y - 2 * c2.center.x * c2.center.x * c1.radius * c1.radius - 2 * c2.center.x * c2.center.x * c2.radius * c2.radius + c2.center.y * c2.center.y * c2.center.y * c2.center.y + 2 * c2.center.y * c2.center.y * c1.radius * c1.radius - 2 * c2.center.y * c2.center.y * c2.radius * c2.radius + c1.radius * c1.radius * c1.radius * c1.radius - 2 * c1.radius * c1.radius * c2.radius * c2.radius + c2.radius * c2.radius * c2.radius * c2.radius)) - 8 * c1.center.x * c1.center.y * c2.center.x + 8 * c1.center.x * c2.center.x * c2.center.y + 4 * c1.center.y * c1.center.y * c1.center.y - 12 * c1.center.y * c1.center.y * c2.center.y + 4 * c1.center.y * c2.center.x * c2.center.x + 12 * c1.center.y * c2.center.y * c2.center.y + 4 * c1.center.y * c1.radius * c1.radius - 4 * c1.center.y * c2.radius * c2.radius - 4 * c2.center.x * c2.center.x * c2.center.y - 4 * c2.center.y * c2.center.y * c2.center.y - 4 * c2.center.y * c1.radius * c1.radius + 4 * c2.center.y * c2.radius * c2.radius) / (2 * (4 * c1.center.x * c1.center.x - 8 * c1.center.x * c2.center.x + 4 * c1.center.y * c1.center.y - 8 * c1.center.y * c2.center.y + 4 * c2.center.x * c2.center.x + 4 * c2.center.y * c2.center.y))
            y2 = c1.center.y - ((4 * c1.center.x * c1.center.x * c1.center.y - 4 * c1.center.x * c1.center.x * c2.center.y + sqrt(Pow((-4 * c1.center.x * c1.center.x * c1.center.y + 4 * c1.center.x * c1.center.x * c2.center.y + 8 * c1.center.x * c1.center.y * c2.center.x - 8 * c1.center.x * c2.center.x * c2.center.y - 4 * c1.center.y * c1.center.y * c1.center.y + 12 * c1.center.y * c1.center.y * c2.center.y - 4 * c1.center.y * c2.center.x * c2.center.x - 12 * c1.center.y * c2.center.y * c2.center.y - 4 * c1.center.y * c1.radius * c1.radius + 4 * c1.center.y * c2.radius * c2.radius + 4 * c2.center.x * c2.center.x * c2.center.y + 4 * c2.center.y * c2.center.y * c2.center.y + 4 * c2.center.y * c1.radius * c1.radius - 4 * c2.center.y * c2.radius * c2.radius), 2) - 4 * (4 * c1.center.x * c1.center.x - 8 * c1.center.x * c2.center.x + 4 * c1.center.y * c1.center.y - 8 * c1.center.y * c2.center.y + 4 * c2.center.x * c2.center.x + 4 * c2.center.y * c2.center.y) * (c1.center.x * c1.center.x * c1.center.x * c1.center.x - 4 * c1.center.x * c1.center.x * c1.center.x * c2.center.x + 2 * c1.center.x * c1.center.x * c1.center.y * c1.center.y - 4 * c1.center.x * c1.center.x * c1.center.y * c2.center.y + 6 * c1.center.x * c1.center.x * c2.center.x * c2.center.x + 2 * c1.center.x * c1.center.x * c2.center.y * c2.center.y - 2 * c1.center.x * c1.center.x * c1.radius * c1.radius - 2 * c1.center.x * c1.center.x * c2.radius * c2.radius - 4 * c1.center.x * c1.center.y * c1.center.y * c2.center.x + 8 * c1.center.x * c1.center.y * c2.center.x * c2.center.y - 4 * c1.center.x * c2.center.x * c2.center.x * c2.center.x - 4 * c1.center.x * c2.center.x * c2.center.y * c2.center.y + 4 * c1.center.x * c2.center.x * c1.radius * c1.radius + 4 * c1.center.x * c2.center.x * c2.radius * c2.radius + c1.center.y * c1.center.y * c1.center.y * c1.center.y - 4 * c1.center.y * c1.center.y * c1.center.y * c2.center.y + 2 * c1.center.y * c1.center.y * c2.center.x * c2.center.x + 6 * c1.center.y * c1.center.y * c2.center.y * c2.center.y + 2 * c1.center.y * c1.center.y * c1.radius * c1.radius - 2 * c1.center.y * c1.center.y * c2.radius * c2.radius - 4 * c1.center.y * c2.center.x * c2.center.x * c2.center.y - 4 * c1.center.y * c2.center.y * c2.center.y * c2.center.y - 4 * c1.center.y * c2.center.y * c1.radius * c1.radius + 4 * c1.center.y * c2.center.y * c2.radius * c2.radius + c2.center.x * c2.center.x * c2.center.x * c2.center.x + 2 * c2.center.x * c2.center.x * c2.center.y * c2.center.y - 2 * c2.center.x * c2.center.x * c1.radius * c1.radius - 2 * c2.center.x * c2.center.x * c2.radius * c2.radius + c2.center.y * c2.center.y * c2.center.y * c2.center.y + 2 * c2.center.y * c2.center.y * c1.radius * c1.radius - 2 * c2.center.y * c2.center.y * c2.radius * c2.radius + c1.radius * c1.radius * c1.radius * c1.radius - 2 * c1.radius * c1.radius * c2.radius * c2.radius + c2.radius * c2.radius * c2.radius * c2.radius))) - 8 * c1.center.x * c1.center.y * c2.center.x + 8 * c1.center.x * c2.center.x * c2.center.y + 4 * c1.center.y * c1.center.y * c1.center.y - 12 * c1.center.y * c1.center.y * c2.center.y + 4 * c1.center.y * c2.center.x * c2.center.x + 12 * c1.center.y * c2.center.y * c2.center.y + 4 * c1.center.y * c1.radius * c1.radius - 4 * c1.center.y * c2.radius * c2.radius - 4 * c2.center.x * c2.center.x * c2.center.y - 4 * c2.center.y * c2.center.y * c2.center.y - 4 * c2.center.y * c1.radius * c1.radius + 4 * c2.center.y * c2.radius * c2.radius) / (2 * (4 * c1.center.x * c1.center.x - 8 * c1.center.x * c2.center.x + 4 * c1.center.y * c1.center.y - 8 * c1.center.y * c2.center.y + 4 * c2.center.x * c2.center.x + 4 * c2.center.y * c2.center.y))
            temp1 = sqrt(c1.radius**2 - (y1 - c1.center.y)**2)
            possible_xs1 = [c1.center.x + temp1, c1.center.x - temp1]
            if are_expressions_approx_equal(y1, y2):
                ret.extend([Point(possible_xs1[0], y1), Point(possible_xs1[1], y2)])
                return ret

            temp2 = sqrt(c2.radius**2 - (y1 - c2.center.y)**2)
            possible_xs2 = [c2.center.x + temp2, c2.center.x - temp2]
            for cur_x1 in possible_xs1:
                for cur_x2 in possible_xs2:
                    if are_expressions_approx_equal(cur_x1, cur_x2):
                        x1 = cur_x1
                        break

            temp1 = sqrt(c1.radius**2 - (y2 - c1.center.y)**2)
            temp2 = sqrt(c2.radius**2 - (y2 - c2.center.y)**2)
            possible_xs1 = [c1.center.x + temp1, c1.center.x - temp1]
            possible_xs2 = [c2.center.x + temp2, c2.center.x - temp2]
            for cur_x1 in possible_xs1:
                for cur_x2 in possible_xs2:
                    if are_expressions_approx_equal(cur_x1, cur_x2):
                        x2 = cur_x1
                        break
            ret.extend([Point(x1, y1), Point(x2, y2)])
        elif simplify(Point.dist(c1.center, c2.center) - (c1.radius + c2.radius)) == 0:
            # In this case, there will be one intersection point
            center_line = Line(c1.center, c2.center)
            delta_x = sqrt(c1.radius**2/(1 + center_line.slope**2))
            if c1.center.x < c2.center.x:
                x = c1.center.x + delta_x
            else:
                x = c1.center.x - delta_x
            ret.extend([center_line.at(x)])
        return ret

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
