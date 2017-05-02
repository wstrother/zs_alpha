import pygame
from math import pi, cos, sin, atan2
from classes import MessageLogger


class Rect:
    RECT_COLOR = 0, 255, 125

    def __init__(self, size, position):
        self.size = size
        self.position = position

    def __repr__(self):
        return "Rect: {}, {}".format(self.size, self.position)

    def draw(self, screen, offset=(0, 0)):
        r = self.pygame_rect
        color = self.RECT_COLOR

        r.x += offset[0]
        r.y += offset[1]

        pygame.draw.rect(
            screen, color,
            r, 1
        )

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y

    @property
    def pygame_rect(self):
        r = pygame.Rect(
            self.position, self.size
        )

        return r

    @property
    def clip(self):
        return self.pygame_rect.clip

    @property
    def copy(self):
        return self.pygame_rect.copy

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, value):
        self.size = value, self.size[1]

    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, value):
        self.size = self.size[0], value

    @property
    def right(self):
        return self.position[0] + self.width

    @right.setter
    def right(self, value):
        dx = value - self.right
        self.move((dx, 0))

    @property
    def left(self):
        return self.position[0]

    @left.setter
    def left(self, value):
        dx = value - self.left
        self.move((dx, 0))

    @property
    def top(self):
        return self.position[1]

    @top.setter
    def top(self, value):
        dy = value - self.top
        self.move((0, dy))

    @property
    def bottom(self):
        return self.top + self.height

    @bottom.setter
    def bottom(self, value):
        dy = value - self.bottom
        self.move((0, dy))

    @property
    def midleft(self):
        return self.left, self.top + (self.height / 2)

    @property
    def topleft(self):
        return self.left, self.top

    @property
    def midtop(self):
        return self.left + (self.width / 2), self.top

    @property
    def topright(self):
        return self.right, self.top

    @property
    def midright(self):
        return self.right, self.top + (self.height / 2)

    @property
    def bottomleft(self):
        return self.left, self.bottom

    @property
    def midbottom(self):
        return self.left + (self.width / 2), self.bottom

    @property
    def bottomright(self):
        return self.right, self.bottom

    @property
    def center(self):
        return (self.left + (self.width / 2),
                self.top + (self.height / 2))

    @center.setter
    def center(self, value):
        x, y = value
        x -= self.width / 2
        y -= self.height / 2

        self.position = x, y

    def get_rect_collision(self, other):
        try:
            collision = self.clip(other.pygame_rect)

            if not (collision.width or collision.height):
                return False

            else:
                return collision.center

        except ValueError:
            return False


class Vector:
    def __init__(self, name, i_hat, j_hat):
        self.name = name
        self.i_hat = i_hat
        self.j_hat = j_hat

        self._log = MessageLogger()
        self.log = self._log.log
        self.get_message = self._log.get_message

    def __repr__(self):
        name = self.name
        i, j = self.get_value()

        return "Vector {}: {}i, {}j".format(name, i, j)

    def get_value(self):
        return self.i_hat, self.j_hat

    def get_draw_point(self, origin=(0, 0), buffer=0):
        ox, oy = origin
        fx, fy = self.apply_to_point(origin)

        q = self.get_quadrant()

        if q == 1:
            return ox - buffer, fy - buffer

        if q == 2:
            return fx - buffer, fy - buffer

        if q == 3:
            return fx - buffer, oy - buffer

        if q == 4:
            return ox - buffer, oy - buffer

        else:
            raise ValueError("get quadrant: {}".format(q))

    def add_vector(self, vector):
        c = self.complex + vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

        return self

    def scale(self, scalar):
        self.i_hat *= scalar
        self.j_hat *= scalar

    def scale_in_direction(self, angle, scalar):
        i, j = self.get_basis_vectors(angle)
        m1 = Matrix.get_from_vectors(i, j)

        m2 = Matrix([
            [scalar, 0],
            [0, 1]
        ])
        m = Matrix(m2.multiply_matrix(m1))

        i, j = m.multiply_vector(self)
        self.i_hat = i
        self.j_hat = j
        self.rotate(angle)

    @staticmethod
    def get_basis_vectors(angle):
        angle *= -1
        i = Vector("basis_i", 1, 0).rotate(angle)
        j = Vector("basis_j", 0, 1).rotate(angle)

        return i, j

    def multiply(self, vector):
        c = self.complex * vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

        return self

    # Returns the vector's angle in Tau * Radians
    def get_angle(self):
        i, j = self.get_value()
        angle = atan2(-j, i) / (2 * pi)     # NOTE: Multiply j value by -1 because down is positive

        if angle >= 0:
            theta = angle

        else:
            theta = 1 + angle

        return theta

    def get_quadrant(self):
        theta = self.get_angle()

        if 0 <= theta < .25:
            return 1

        if .25 <= theta < .5:
            return 2

        if .5 <= theta < .75:
            return 3

        if .75 <= theta <= 1:
            return 4

        else:
            raise ValueError("angle {}".format(theta))

    # Alters vector values in place to make its angle match a given value in Tau * Radians
    def set_angle(self, angle):
        theta = self.get_angle()
        delta = angle - theta
        self.rotate(delta)

    # Alters vector values in place to rotate its angle by a given Tau * Radians value
    def rotate(self, theta):
        theta *= (2 * pi)
        i, j = cos(theta), sin(theta)

        self.multiply(Vector("rotation", i, -j))

        return self

    # Returns the vector's displacement values applied to a point.
    def apply_to_point(self, point=(0, 0)):
        x, y = point
        x += self.i_hat
        y += self.j_hat

        return x, y

    def get_copy(self, rotate=0.0, scale=1):
        v = Vector(self.name, self.i_hat, self.j_hat)

        if rotate:
            v.rotate(rotate)

        v.scale(scale)

        return v

    # Alter vector values in place
    def set_value(self, i_hat, j_hat):
        self.i_hat = i_hat
        self.j_hat = j_hat

    @staticmethod
    def get_from_complex(c):
        i, j = c.real, c.imag

        return Vector("", i, j)

    @property
    def complex(self):
        return complex(self.i_hat, self.j_hat)

    @property
    def magnitude(self):
        return abs(self.complex)

    # Returns False if the angle is vertical.
    def get_y_intercept(self, origin):
        if self.i_hat == 0:                         # no Y-intercept for vertical lines
            return False

        if self.j_hat == 0:
            return origin[1]                        # horizontal line just returns y value

        slope = self.j_hat / self.i_hat
        x0, y0 = origin

        c = y0 - (slope * x0)

        return c

    def check_orientation(self, vector):
        t1, t2 = self.get_angle(), vector.get_angle()

        def compare_angles(a1, a2):
            top = a1 + .25
            bottom = a1 - .25

            return bottom < a2 < top

        if .25 <= t1 < .75:
            return compare_angles(t1, t2)

        elif t1 < .25:
            return compare_angles(
                t1 + .25, (t2 + .25) % 1)

        elif .75 <= t1:
            return compare_angles(
                t1 - .25, (t2 - .25) % 1)


class Wall(Vector):
    def __init__(self, name, origin, end):
        ox, oy = origin
        fx, fy = end
        i = fx - ox
        j = fy - oy
        super(Wall, self).__init__(name, i, j)

        self.origin = origin

    def __repr__(self):
        name = self.name
        origin = tuple(self.origin)
        angle = self.get_angle()
        end = self.apply_to_point(self.origin)

        return "Wall: {} angle: {}, {} to {}".format(
            name, angle, origin, end)

    @property
    def end_point(self):
        return self.apply_to_point(self.origin)

    @staticmethod
    def get_from_vector(vector, origin=(0, 0)):
        i, j = vector.get_value()
        ox, oy = origin
        i += ox
        j += oy

        origin = ox, oy
        end = i, j

        return Wall(vector.name, origin, end)

    def get_rect(self):
        w, h = self.get_value()
        w = abs(w)
        h = abs(h)

        if w < 1:
            w = 1
        if h < 1:
            h = 1

        ox, oy = self.origin
        fx, fy = self.apply_to_point(self.origin)
        px, py = ox, oy

        if ox > fx:
            px = fx

        if oy > fy:
            py = fy

        return Rect((w, h), (px, py))

    def get_normal(self):
        normal = Vector(self.name + " normal force", 1, 0)
        normal.set_angle(self.get_angle())
        normal.rotate(.25)

        return normal

    def get_copy(self, rotate=0.0, scale=1):
        v = super(Wall, self).get_copy(rotate=rotate, scale=scale)

        return Wall.get_from_vector(v, self.origin)

    def rotate_around(self, point, angle):
        px, py = point
        ox, oy = self.origin
        dx = ox - px
        dy = oy - py

        d = Vector("displacement", dx, dy)
        d.rotate(angle)
        self.rotate(angle)

        self.origin = d.apply_to_point(point)

    # Returns the collision point for the underlying axes of two vector objects.
    # Returns False if the axes are parallel.
    def axis_collision(self, wall, origin=False):
        if origin:
            w = Wall.get_from_vector(wall, origin)
        else:
            w = wall.get_copy()

        delta = .75 - self.get_angle()                  # defines offset angle from y-axis

        w.rotate_around(self.origin, delta)             # rotate other vector about the origin
        wx, wy = w.origin
        wx -= self.origin[0]

        y_int = w.get_y_intercept((wx, wy))             # get the y-intercept of the other vector

        if y_int is False:
            return False

        y_int -= self.origin[1]

        collision = Vector("collision", 0, y_int)
        collision.rotate(-delta)                        # rotate back around to the original angle

        return collision.apply_to_point(self.origin)    # output the offset of other vector to first vector's origin

    # Returns the collision point of two vectors. Returns False if the two vectors are parallel
    def vector_collision(self, vector, origin):
        axis_collision = self.axis_collision(vector, origin)      # get axis collision...

        if not axis_collision:
            return False

        def point_in_bounds(w):
            x, y = axis_collision
            sx, sy = w.origin
            fx, fy = w.apply_to_point(
                w.origin)

            if fx > sx:
                x_bound = sx - 1 <= x <= fx + 1
            else:
                x_bound = sx + 1 >= x >= fx - 1
            if fy > sy:
                y_bound = sy - 1 <= y <= fy + 1
            else:
                y_bound = sy + 1 >= y >= fy - 1

            return x_bound and y_bound

        wall = Wall.get_from_vector(vector, origin)
        if point_in_bounds(self) and point_in_bounds(wall):
            return axis_collision                                  # check if it's within the bounds of both vectors

        else:
            return False

    def get_normal_adjustment(self, point):
        x, y = point
        normal = self.get_normal()
        nx, ny = self.axis_collision(
            normal, (x, y))

        dx = x - nx
        dy = y - ny
        adjustment = Vector("position adjustment", -dx, -dy)

        return adjustment.get_value()


class Matrix:
    # [[a, c],
    #  [b, d]]
    # i_hat = ax + by       ae + bg     af + bh
    # j_hat = cx + dy       ce + dg     cf + dh
    def __init__(self, values):
        self.values = values

        self.a, self.b = values[0]
        self.c, self.d = values[1]

    @staticmethod
    def get_from_vectors(i, j):
        m = [
            [i.i_hat, j.i_hat],
            [i.j_hat, j.j_hat]
        ]
        return Matrix(m)

    def get_vectors(self):
        return (
            Vector("i_hat", self.a, self.c),
            Vector("j_hat", self.b, self.d)
        )

    def multiply_vector(self, vector):
        x, y = vector.get_value()
        ax = self.a * x
        by = self.b * y
        cx = self.c * x
        dy = self.d * y
        i = ax + by
        j = cx + dy

        return i, j

    def multiply_matrix(self, matrix):
        i, j = matrix.get_vectors()

        new_i = self.multiply_vector(i)
        new_j = self.multiply_vector(j)

        values = [
            [new_i[0], new_j[0]],
            [new_i[1], new_j[1]]
        ]

        return values

