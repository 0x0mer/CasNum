from .point import Point
from .line import Line
from .circle import Circle

def get_perpendicular_bisector(l):
    c1 = Circle(l.p1, l.p2)
    c2 = Circle(l.p2, l.p1)
    return Line(*c1.intersect(c2))

def get_midpoint(l):
    l_perp = get_perpendicular_bisector(l)
    return l.intersect(l_perp)

def generate_n(n, origin=Point(0,0), unit=Point(1,0)):
    l = Line(origin, unit)
    p_cur = unit
    p_prev = origin
    for _ in range(n):
        c = Circle(p_cur, p_prev)
        p1, p2 = c.intersect_with_line(l)
        if p_prev.isEqual(p1):
            p_prev = p_cur
            p_cur = p2
        else:
            p_prev = p_cur
            p_cur = p1
    return p_prev

def get_perpendicular_to_line_through_point(p, l):
    if l.dist_from_point(p) > 0:
        c = Circle(p, l.p1)
        inter = c.intersect_with_line(l)
        if len(inter) < 2:
            c = Circle(p, l.p2)
            inter = c.intersect_with_line(l)
        p1, p2 = inter
        c1 = Circle(p1, p)
        c2 = Circle(p2, p)
        p1, p2 = c1.intersect(c2)
        return Line(p1, p2)
    else:
        if p.isEqual(l.p1):
            c = Circle(p, l.p2)
        else:
            c = Circle(p, l.p1)
        p1, p2 = c.intersect_with_line(l)
        l1 = get_perpendicular_bisector(Line(p, p1))
        l2 = get_perpendicular_bisector(Line(p, p2))
        p11, p12 = c.intersect_with_line(l1)
        p21, p22 = c.intersect_with_line(l2)
        if Point.dist(p11, p21) < Point.dist(p11, p22):
            return get_perpendicular_bisector(Line(p11, p21))
        else:
            return get_perpendicular_bisector(Line(p12, p22))


def get_parallel_to_line_through_point(p, l):
    l_perp = get_perpendicular_to_line_through_point(p, l)
    p_tag = l.intersect(l_perp)
    c = Circle(p, p_tag)
    return get_perpendicular_bisector(Line(*c.intersect_with_line(l_perp)))

def get_y_axis(origin, unit):
    return get_perpendicular_to_line_through_point(origin, Line(origin, unit))

def mirror_point(p, l):
    l_perp = get_perpendicular_to_line_through_point(p,l)
    a = l.intersect(l_perp)
    p1, p2 = Circle(a, p).intersect_with_line(l_perp)
    if p1.isEqual(p):
        return p2
    else:
        return p1

def mirror_point_on_x_axis(p, origin):
    if p.isEqual(origin):
        return origin
    c = Circle(origin, p)
    p1, p2 = c.intersect_with_line(Line(origin, p))
    return p1 if p2.isEqual(p) else p2


def double_point_on_x_axis(origin, p):
    if p.isEqual(origin):
        return origin
    c = Circle(p, origin)
    p1, p2 = c.intersect_with_line(Line(origin, p))
    return p1 if p2.isEqual(origin) else p2

def half_point_on_x_axis(origin, p):
    if p.isEqual(origin):
        return origin
    return get_midpoint(Line(origin, p))
