from entities import Sprite
from animation import AnimationGraphics, AnimationMachine, UdlrAnimationMachine
from zs_constants import UDLR, UDLR_VALUE
from geometry import Rect, Wall
from physics import PhysicsInterface

from math import sqrt

ANIMATION_CLASS_DICT = {
    "animation_machine": AnimationMachine,
    "udlr_machine": UdlrAnimationMachine
}

BASE_SPEED = 2.5


class AnimationSprite(Sprite):
    def __init__(self, name):
        super(AnimationSprite, self).__init__(name)

        self.animation_machine = None
        self.face_direction = 1, 0
        self.base_speed = BASE_SPEED

        self.movement_table = {
            "walk": 1,
        }

        self.direction_table = {
            "walk": True,
            "idle": True
        }

        self.physics_interface = PhysicsInterface(self)
        self.physics_interface.set_interface()

        self.hitbox_manager = HitboxManager(self)

    def get_collision_skeleton(self):
        rect = self.get_collision_rect()

        mt = rect.midtop
        mb = rect.midbottom
        ml = rect.midleft
        mr = rect.midright

        h = Wall(self.name + " h skeleton", ml, mr)
        v = Wall(self.name + " v skeleton", mt, mb)

        return h, v

    def get_last_position(self):
        return self.physics_interface.last_position

    def get_collision_rect(self):
        rect = self.get_animation_object("body")
        last = self.physics_interface.get_instantaneous_velocity()
        last.rotate(.5)
        rect.center = last.apply_to_point(rect.center)

        return rect

    def get_collision_points(self):
        rect = self.get_collision_rect()

        return [
            rect.midtop, rect.midright,
            rect.midleft, rect.midbottom,
            rect.center
        ]

    def get_collision_point(self):
        return self.get_collision_points()[0]

    def get_animation_state(self):
        return self.animation_machine.get_animation_state()

    def get_animation_object(self, key):
        if self.animation_machine:
            a = self.animation_machine.get_animation()
            scale = self.graphics.scale

            ox, oy, w, h = a[key]
            ox *= scale
            oy *= scale
            w *= scale
            h *= scale

            x, y = self.rect.topleft
            x += ox
            y += oy

            return Rect((w, h), (x, y))

        else:
            return self.rect

    def set_base_speed(self, value):
        self.base_speed = value

    def set_movement_table(self, table):
        self.movement_table = table

    def set_direction_table(self, table):
        self.direction_table = table

    def set_animation(self, d):
        transition_file = d["state_transitions"]

        sprite_sheet = d["sprite_sheet"]
        image_layers = d.get("sprite_sheet_layer", [])
        if image_layers:
            image_layers = [image_layers]

        scale = d.get("scale", 1)

        self.set_graphics(AnimationGraphics, sprite_sheet, scale)

        for layer in image_layers:
            image, x, y = layer
            position = x, y
            self.graphics.add_image_layer(image, position)

        cls = d.get("class")
        if not cls:
            self.animation_machine = AnimationMachine(self)

        else:
            cls = ANIMATION_CLASS_DICT[cls]
            self.animation_machine = cls(self)

        self.animation_machine.set_transitions(self, transition_file)

        animation_file = d.get("animations")
        if not animation_file:
            animation_file = transition_file[:-4] + "_animation.cfg"

        self.animation_machine.set_animations(animation_file)
        self.graphics.set_animations(
            self.animation_machine.animations
        )

    # UPDATE ROUTINE METHODS

    def get_update_methods(self):
        um = super(AnimationSprite, self).get_update_methods()

        if self.animation_machine:
            um += [
                self.animation_machine.update,
                self.update_face_direction,
                self.handle_movement,
                self.physics_interface.update,
                self.handle_sounds
            ]

        return um

    def update_face_direction(self):
        controller = self.controller
        machine = self.animation_machine

        if controller and machine:
            dpad = controller.get_device("Dpad")

            state = machine.get_state()
            face = self.direction_table

            if state in face:
                if dpad.held:
                    self.face_direction = dpad.get_direction()

    def handle_movement(self):
        controller = self.controller
        machine = self.animation_machine

        if controller and machine:
            state = machine.get_state()
            dpad = controller.get_device("Dpad")

            base_speed = self.base_speed
            move = self.movement_table

            if state in move:
                base_speed *= move[state]

                x, y = dpad.get_direction()

                if x and y:
                    base_speed *= sqrt(.5)

                x *= base_speed
                y *= base_speed

                self.physics_interface.apply_force(x, y)

    def handle_sounds(self):
        sounds = self.sounds
        machine = self.animation_machine

        state = machine.get_state()

        d = machine.get_animation()
        sound_frame = d.get("sound_frame", 0)
        state_frame = machine.get_state_frame()
        ani_frame = machine.get_animation_frame()
        l = len(d["frames"])

        hear = sound_frame == ani_frame and state_frame % l == 0

        if state in sounds and hear:
            if not d.get("sound_overlap", True):
                sounds[state].stop()
            sounds[state].play()

        last = machine.last_state

        if last in sounds:
            d = machine.get_animation(state=last)

            if d.get("sound_cutoff", False):
                sounds[last].stop()

    # def get_animation_state(self):
    #     return self.animation_machine.get_state()

    def get_dir_string(self, direction=None):
        if not direction:
            direction = self.face_direction

        try:
            i = UDLR_VALUE.index(direction)
        except ValueError:
            if direction[0] == 1:
                i = 3
            else:
                i = 2

        return UDLR[i]

    @property
    def draw_point(self):
        w, h = self.size

        w /= 2
        h /= 2

        x, y = self.position

        x -= w
        y -= h

        return x, y

    def get_position(self):
        return self.rect.center

    def set_position(self, x, y):
        self.rect.center = (x, y)

    def on_spawn(self):
        self.animation_machine.set_state("idle")


class HitboxManager:
    def __init__(self, entity):
        self.entity = entity

    def get_hitbox_collisions(self, other):
        hitboxes = self.entity.animation_machine.get_hitboxes()
        hurtboxes = other.animation_machine.get_hitboxes(key="hurtbox")
        rects = [other.get_collision_rect()] + hurtboxes

        collisions = []

        for h in hitboxes:
            if "size" in h:
                r = Rect(h["size"], h["position"])

                collision = any(
                    [r.get_rect_collision(o) for o in rects]
                )

                if collision:
                    collisions.append(h)

            if "radius" in h:
                r = other.get_collision_rect()
                radius = h["radius"]
                position = h["position"]

                collision = any(
                    [r.get_circle_collision(radius, position) for r in rects]
                )

                if collision:
                    collisions.append(h)

        return collisions

    def handle_hitboxes(self, hitboxes):
        print("\n---")
        for h in hitboxes:
            print(h)

        self.entity.animation_machine.set_state("hurt")

    @staticmethod
    def do_hitbox_collision(sprite, other):
        s_collisions = sprite.hitbox_manager.get_hitbox_collisions(other)
        o_collisions = other.hitbox_manager.get_hitbox_collisions(sprite)

        if s_collisions:
            other.hitbox_manager.handle_hitboxes(s_collisions)

        if o_collisions:
            sprite.hitbox_manager.handle_hitboxes(o_collisions)
