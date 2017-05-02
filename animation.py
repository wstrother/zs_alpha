import pygame

from classes import StateMachine
from graphics import Graphics, ImageGraphics
from resources import load_resource
from zs_cfg import print_dict
from zs_constants import UDLR


class AnimationGraphics(Graphics):
    def __init__(self, entity, sprite_sheet, scale=1):
        super(AnimationGraphics, self).__init__(entity)

        sprite_sheet = load_resource(sprite_sheet)
        w, h = sprite_sheet.get_size()

        # PYGAME CHOKE POINT
        self.scale = scale

        if scale > 1:
            w *= scale
            h *= scale

            sprite_sheet = pygame.transform.scale(sprite_sheet, (w, h))

        self.sprite_sheet = sprite_sheet
        self.mirror_sheet = self.mirror_image(sprite_sheet)

        ImageGraphics.set_colorkey(self.sprite_sheet)
        ImageGraphics.set_colorkey(self.mirror_sheet)

        self.image_sets = {}

    @staticmethod
    def mirror_image(image):
        # PYGAME CHOKE POINT

        return pygame.transform.flip(image, True, False)

    def add_image_layer(self, file_name, position=(0, 0)):
        image_layer = load_resource(file_name)
        ImageGraphics.set_colorkey(image_layer)

        # PYGAME CHOKE POINT

        scale = self.scale
        w, h = image_layer.get_size()

        if scale > 1:
            w *= scale
            h *= scale

            image_layer = pygame.transform.scale(image_layer, (w, h))

        x, y = position
        x *= scale
        y *= scale

        self.sprite_sheet.blit(image_layer, (x, y))
        self.mirror_sheet = self.mirror_image(self.sprite_sheet)

    def get_image(self):
        machine = self.entity.animation_machine

        image_set = self.get_image_set(
            machine.get_animation_state()
        )

        if image_set:
            return image_set[machine.get_animation_frame()]

    def get_image_set(self, state):
        if state in self.image_sets:
            return self.image_sets[state]

        elif "default" in self.image_sets:
            return self.image_sets["default"]

    def reset_image(self):
        machine = self.entity.animation_machine

        if machine:
            w, h = machine.get_animation()["size"]
            w *= self.scale
            h *= self.scale

            rect = self.entity.rect
            cx, cy = rect.center
            rect.size = w, h
            rect.center = cx, cy

    def set_animations(self, animations):
        for name in animations:
            if "mirror" in animations[name]:
                sprite_sheet = self.mirror_sheet

            else:
                sprite_sheet = self.sprite_sheet

            self.image_sets[name] = self.make_image_set(
                sprite_sheet, animations[name], scale=self.scale
            )

    @staticmethod
    def make_image_set(sprite_sheet, animation, scale=1):
        print(animation)
        mirror = animation.get("mirror", False)
        cell_size = animation["size"]
        start = animation["start_index"]

        images = []
        w, h = cell_size
        w *= scale
        h *= scale

        sx, sy = start
        sx *= scale
        sy *= scale

        sheet_w, sheet_h = sprite_sheet.get_size()

        for frame in animation["frames"]:
            x, y = frame
            x *= w
            y *= h

            px, py = x + sx, y + sy
            if mirror:
                px = (sheet_w - w) - px
            position = px, py

            # PYGAME CHOKE POINT

            r = pygame.Rect(position, (w, h))
            print(r)
            print(sprite_sheet)
            cell = sprite_sheet.subsurface(r)
            images += [cell]

        return images


class AnimationMachine(StateMachine):
    def __init__(self, entity):
        super(AnimationMachine, self).__init__(entity.name)
        self.entity = entity

        self.state_frame = -1
        self.animations = {}
        self.hitboxes = {}
        self.last_state = None

    def get_hitboxes_from_cfg(self, cfg):
        hitboxes = cfg["hitboxes"]
        for name in hitboxes:
            hitboxes[name]["name"] = name

        new = {}
        for animation in self.animations:
            names = [
                k for k in hitboxes if animation in k           # direction variations on name
            ]

            for name in names:
                new_entry = {}
                entry = hitboxes[name]                          # specific directional animation dict

                for key in entry:
                    value = entry[key]

                    if type(value) is list:
                        new_value = []
                        value = [hitboxes[k] for k in value]

                        new_entry[key] = value                  # final hitbox_dict only has keys for frames

                new[name] = new_entry                           # that have hitboxes

        return new

    def get_hitboxes(self):
        frame = self.get_animation_frame()
        name = self.get_animation_state()
        scale = self.entity.graphics.scale
        px, py = self.entity.rect.topleft

        d = False

        if name in self.hitboxes:
            d = self.hitboxes[name]

        if d and frame in d:
            output = []

            for hitbox in d[frame]:
                entry = {"name": hitbox["name"]}

                if "size" in hitbox:
                    w, h = hitbox["size"]
                    w *= scale
                    h *= scale

                    entry["size"] = w, h

                if "radius" in hitbox:
                    entry["radius"] = hitbox["radius"] * scale

                if "position" in hitbox:
                    x, y = hitbox["position"]
                    x *= scale
                    x += px
                    y *= scale
                    y += py

                    entry["position"] = x, y

                output.append(entry)

            return output

    def get_animation(self, state=None):
        if not state:
            state = self.get_animation_state()

        if state in self.animations:
            return self.animations[state]

        else:
            return self.animations[
                self.get_default_state()]

    def get_default_state(self):
        return "idle"

    def get_animation_state(self):
        state = self.get_state()

        return state

    def get_animation_frame(self):
        d = self.get_animation()

        fl = d["frame_length"]
        sf = self.get_state_frame()

        l = len(d["frames"])

        return (sf // fl) % l

    def get_state_frame(self):
        return self.state_frame

    def animation_complete(self):
        animation = self.get_animation()
        l = len(animation["frames"]) * animation["frame_length"] - 1

        return self.get_state_frame() >= l

    def set_state(self, state):
        self.last_state = self.get_state()

        super(AnimationMachine, self).set_state(state)

        if self.entity.graphics:
            self.entity.graphics.reset_image()

        self.reset_animation()

    def set_animations(self, file_name):
        cfg = load_resource(file_name)
        self.animations = self.get_animations_from_cfg(cfg)

        if "hitboxes" in cfg:
            self.hitboxes = self.get_hitboxes_from_cfg(cfg)

    def get_animations_from_cfg(self, cfg):
        animations = {}
        for name in cfg["animations"]:
            d = {}
            entry = cfg["animations"][name]

            d["frame_length"] = entry.get("frame_length", 1)
            d["start_index"] = entry.get("start_index", (0, 0))
            d["frames"] = self.get_frames_from_entry(entry)

            for key in entry:
                if not type(key) is int:
                    d[key] = entry[key]

            animations[name] = d

        return animations

    @staticmethod
    def get_frames_from_entry(entry):
        indexes = sorted([k for k in entry if type(k) is int])
        frames = [tuple(entry[i]) for i in indexes]

        return frames

    def reset_animation(self):
        self.state_frame = -1

    def update(self):
        super(AnimationMachine, self).update()

        self.state_frame += 1

    def auto(self):
        return self.animation_complete()


class UdlrAnimationMachine(AnimationMachine):
    def get_animation_state(self):
        return self.get_direction_state_string()

    def get_direction_state_string(self, state=None):
        if not state:
            state = self.get_state()

        return state + "_" + self.entity.get_dir_string()

    def get_animation(self, state=None):
        if state in self.animations:
            return super(UdlrAnimationMachine, self).get_animation(state)

        else:
            return super(UdlrAnimationMachine, self).get_animation(
                self.get_direction_state_string(state)
            )

    def get_animations_from_cfg(self, cfg):
        animations = {}

        for name in cfg["animations"]:
            d_up = {}
            d_down = {}
            d_left = {}
            d_right = {}

            def add_to_dicts(key, value):
                for d in (d_up, d_down, d_left, d_right):
                    d[key] = value

            entry = cfg["animations"][name]

            add_to_dicts("frame_length", entry.get("frame_length", 1))
            add_to_dicts("start_index", entry.get("start_index", (0, 0)))

            frames = self.get_frames_from_entry(entry)
            d_up["frames"] = frames
            d_down["frames"] = [(x, y + 1) for x, y in frames]
            d_right["frames"] = [(x, y + 2) for x, y in frames]

            mirror = entry.get("mirror", True)

            if mirror:
                d_left["frames"] = [(x, y + 2) for x, y in frames]
                d_left["mirror"] = True
                if "mirror" in entry:
                    entry.pop("mirror")
            else:
                d_left["frames"] = [(x, y + 3) for x, y in frames]

            for key in entry:
                if not type(key) is int:
                    add_to_dicts(key, entry[key])

            names = [name + "_" + UDLR[i] for i in range(4)]

            i = 0
            for d in (d_up, d_down, d_left, d_right):
                animations[names[i]] = d
                i += 1

        return animations

    def get_default_state(self):
        return self.get_direction_state_string(
            super(UdlrAnimationMachine, self).get_default_state()
        )
