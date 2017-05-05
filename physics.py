from geometry import Vector


class PhysicsInterface:
    def __init__(self, entity):
        self.entity = entity

        self.mass = 1
        self.elasticity = 1
        self.gravity = 0
        self.friction = .75

        self.velocity = Vector(entity.name + " velocity", 0, 0)
        self.forces = []
        self.last_position = 0, 0

    def set_interface(self):
        entity = self.entity

        entity.get_velocity = self.get_instantaneous_velocity
        entity.set_gravity = self.set_gravity
        entity.set_friction = self.set_friction
        entity.set_mass = self.set_mass
        entity.set_elasticity = self.set_elasticity
        entity.apply_force = self.apply_force
        entity.scale_movement_in_direction = self.scale_movement_in_direction

    def get_instantaneous_velocity(self):
        entity = self.entity
        x, y = entity.position
        lx, ly = self.last_position

        x -= lx
        y -= ly

        return Vector(entity.name + " instantaneous velocity", x, y)

    def set_mass(self, value):
        self.mass = value

    def set_elasticity(self, value):
        self.elasticity = value

    def set_gravity(self, value):
        self.gravity = value

    def set_friction(self, value):
        self.friction = value

    def scale_movement_in_direction(self, angle, value):
        self.velocity.scale_in_direction(angle, value)

    def apply_force(self, i, j):
        self.forces.append(
            Vector("acceleration force", i, j)
        )

    def integrate_forces(self):
        forces = self.forces
        self.forces = []

        i, j = 0, 0

        for f in forces:
            i += f.i_hat
            j += f.j_hat

        self.velocity.i_hat += i
        self.velocity.j_hat += j

    def apply_velocity(self):
        if self.mass:
            movement = self.velocity.get_copy(
                scale=(1 / self.mass)).get_value()
            self.entity.move(movement)

    def update(self):
        self.last_position = self.entity.position
        self.integrate_forces()

        # friction
        self.velocity.scale(self.friction)

        # gravity
        if self.gravity:
            g = self.gravity * self.mass
            self.apply_force(0, g)

        # movement
        self.apply_velocity()

    @staticmethod
    def wall_velocity_test(wall, sprite):
        n = wall.get_normal()
        n.rotate(.5)

        points = sprite.get_collision_points()
        v = sprite.get_velocity()

        if n.check_orientation(v):
            for point in points:
                collision = wall.vector_collision(v, point)

                if collision:
                    return point

    @staticmethod
    def test_wall_collision(wall, sprite):
        v_test = PhysicsInterface.wall_velocity_test(wall, sprite)

        if v_test:
            return v_test

        else:
            s_test = PhysicsInterface.wall_skeleton_test(wall, sprite)

            return s_test

    @staticmethod
    def wall_skeleton_test(wall, sprite):
        v = sprite.get_velocity()
        n = wall.get_normal()

        if not n.check_orientation(v):
            skeleton = sprite.get_collision_skeleton()
            angle = n.get_angle() + .5

            r = (0 <= angle < .125) or (.875 <= angle <= 1)
            t = .125 <= angle < .375
            l = .375 <= angle < .675
            b = .675 <= angle < .875

            h = l or r
            v = t or b

            if h:
                w = skeleton[0]
                collision = wall.vector_collision(w, w.origin)

                if collision:
                    if l:
                        return w.origin

                    if r:
                        return w.end_point
            if v:
                w = skeleton[1]
                collision = wall.vector_collision(w, w.origin)

                if collision:
                    if t:
                        return w.origin

                    if b:
                        return w.end_point

    @staticmethod
    def smooth_wall_collision(wall, sprite, point):
        v = sprite.get_velocity()

        sprite.move(
            wall.get_normal_adjustment(
                v.apply_to_point(point)
            )
        )

        normal = wall.get_normal()
        sprite.scale_movement_in_direction(
            normal.get_angle(), 0)

    @staticmethod
    def bounce_wall_collision(wall, sprite, point):
        v = sprite.get_velocity()

        sprite.move(
            wall.get_normal_adjustment(
                v.apply_to_point(point)
            )
        )

        normal = wall.get_normal()
        sprite.scale_movement_in_direction(
            normal.get_angle(), -1)

    @staticmethod
    def test_sprite_collision(sprite, other):
        r1 = sprite.get_collision_rect()
        r2 = other.get_collision_rect()

        return r1.get_rect_collision(r2)

    @staticmethod
    def handle_sprite_collision(sprite, other, collision):
        if collision:
            def check_orientation(s):
                x, y = s.get_collision_rect().center
                cx, cy = collision
                heading = Vector("heading", cx - x, cy - y)

                return s.get_velocity().check_orientation(heading)

            def get_adjustment(o):
                x, y = o.get_collision_rect().center
                cx, cy = collision
                v = Vector("collision adjustment", cx - x, cy - y)

                return v

            def do_adjustment(s, o):
                v = get_adjustment(o)

                if check_orientation(s):
                    s.scale_movement_in_direction(v.get_angle(), 0)

                v.scale(1 - s.physics_interface.elasticity)
                s.apply_force(*v.get_value())

            do_adjustment(sprite, other)
            do_adjustment(other, sprite)
