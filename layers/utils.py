from entities import Layer
from graphics import RectGraphics, VectorGraphics
from sprites.menus import PauseMenu
from sprites.gui import VectorSprite
from geometry import Rect, Wall
from classes import Group


class DrawRectLayer(Layer):
    def __init__(self, name):
        super(DrawRectLayer, self).__init__(name)

        self.draw_width = 2
        self.draw_color = 0, 255, 0

        self.get_rect_function = None
        self.rect_args = []
        self.get_items = self.get_items_from_groups

    def update_items(self):
        pass

    def set_draw_color(self, color):
        self.draw_color = color

    def set_draw_width(self, width):
        self.draw_width = width

    def set_rect_function(self, *args):
        method_name = args[0]
        if len(args) > 1:
            args = args[1:]
        else:
            args = []
        self.get_rect_function = getattr(self, method_name)
        self.rect_args = args

    def set_items_function(self, obj, method_name):
        self.get_items = getattr(obj, method_name)

    def get_items_from_groups(self):
        items = []

        for g in self.groups:
            items += [i for i in g]

        return items

    def draw_items(self, canvas, offset=(0, 0)):
        color = self.draw_color
        width = self.draw_width

        for item in self.get_items():
            args = self.rect_args

            if self.get_rect_function:
                r = self.get_rect_function(item, *args)

            else:
                r = item

            if not type(r) is list:
                r = [r]

            for rect in r:
                if type(rect) is not dict:
                    if isinstance(rect, Rect):
                        d = {
                            "class": "rect",
                            "size": rect.size,
                            "position": rect.position
                        }

                    elif isinstance(rect, Wall):
                        d = {
                            "class": "vector",
                            "vector": rect,
                            "position": rect.origin
                        }

                    elif isinstance(rect, VectorSprite):
                        d = {
                            "class": "vector",
                            "vector": rect.vector,
                            "position": rect.vector_origin
                        }

                    else:
                        raise ValueError("bad value type passed {}: \n\t{}".format(
                            str(type(rect)), rect))
                else:
                    d = rect.copy()
                    if "radius" in d:
                        d["class"] = "circle"

                    if "size" in d:
                        d["class"] = "rect"

                d["draw_color"] = color
                d["draw_width"] = width
                self.draw_object_from_dict(canvas, d, offset)

    @staticmethod
    def draw_object_from_dict(canvas, d, offset=(0, 0)):
        color = d["draw_color"]
        width = d["draw_width"]
        x, y = d["position"]
        x += offset[0]
        y += offset[1]

        if d["class"] == "vector":
            image = VectorGraphics.get_vector_image(
                            d["vector"], color, width)
            x, y = d["vector"].get_draw_point((x, y), width)

        elif d["class"] == "rect":
            image = RectGraphics.get_rect_image(
                d["size"], color, width)

        elif d["class"] == "circle":
            image = RectGraphics.get_circle_image(
                d["radius"], color, width)

            w, h = image.get_size()
            x -= w/2
            y -= h/2

        else:
            raise ValueError("bad dict passed")

        # PYGAME CHOKE POINT
        canvas.blit(image, (x, y))

    @staticmethod
    def get_item_rect(item):
        return item.rect

    @staticmethod
    def get_hitboxes(item, *keys):
        if not keys:
            hitboxes = item.animation_machine.get_hitboxes()
        else:
            hitboxes = []

            for key in keys:
                hitboxes += item.animation_machine.get_hitboxes(key=key)

        if not hitboxes:
            return []

        else:
            return hitboxes


class DrawVectorLayer(DrawRectLayer):
    def __init__(self, name):
        super(DrawVectorLayer, self).__init__(name)

        self.vector_scale = 1

    def set_vector_scale(self, value):
        self.vector_scale = value

    def get_item_velocity(self, item):
        v = item.get_velocity().get_copy(scale=self.vector_scale)

        return {
            "class": "vector",
            "vector": v,
            "position": item.get_collision_point()
        }

    @staticmethod
    def get_region_walls(item):
        return item.walls


class PauseMenuLayer(Layer):
    def __init__(self, name):
        super(PauseMenuLayer, self).__init__(name)

        self._game_paused = False
        self._frame_advance = False
        self.pause_menu = None
        self.pause_layers = []
        self.groups = [Group("pause menu group")]

    def set_pause_layers(self, *layers):
        self.pause_layers = layers

    def on_spawn(self):
        self.set_command_inputs("double tap up")

        pm = PauseMenu("Pause Menu")
        self.pause_menu = pm

        pm.set_model(self.model)
        pm.set_controller(self.controller.name)
        pm.set_event_passers(self, "on_exit", "on_frame_advance")

        pm.add_listener("on_death", {
            "name": "on_unpause",
            "target": self
        })

    def update(self):
        super(PauseMenuLayer, self).update()

        if self.controller:
            tap_up = self.controller.check_command("double tap up")

            if self._frame_advance and tap_up:
                self._frame_advance = False
                self.handle_pause()

            start_pressed = self.controller.get_device("Start").check()

            if start_pressed and not self._frame_advance:
                pausing = True

                if self._game_paused:
                    pausing = False

                for layer in self.pause_layers:
                    layer.paused = self._game_paused

                if pausing:
                    self.handle_pause()

                else:
                    self.pause_menu.handle_event("on_unpause")

            if self._frame_advance:
                for layer in self.pause_layers:
                    layer.paused = not start_pressed

    def handle_pause(self):
        self._game_paused = True
        for layer in self.pause_layers:
            layer.paused = True

        pm = self.pause_menu
        pm.set_group(self.groups[0])
        pm.reset_menu()

        if pm.graphics:
            pm.graphics.reset_image()

    def on_unpause(self):
        self._game_paused = False
        for layer in self.pause_layers:
            layer.paused = False

    def on_frame_advance(self):
        self._frame_advance = True


