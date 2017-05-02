from entities import Layer, ModelManager
from graphics import RectGraphics, VectorGraphics
from sprites.menus import PauseMenu
from sprites.gui import HudFieldSprite, ContainerSprite
from geometry import Vector
from classes import Group


class DrawRectLayer(Layer):
    def __init__(self, name):
        super(DrawRectLayer, self).__init__(name)

        self.draw_width = 2
        self.draw_color = 0, 255, 0
        self.get_rect_function = self.get_item_rect
        self.rect_args = []

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

    def draw_items(self, canvas):
        color = self.draw_color
        width = self.draw_width

        for g in self.groups:
            for item in g:
                args = self.rect_args
                r = self.get_rect_function(item, *args)

                if not type(r) is list:
                    r = [r]

                for rect in r:
                    if type(rect) is dict:
                        if "radius" in rect:
                            self.draw_circle(
                                canvas, rect["radius"],
                                rect["position"],
                                color, width)
                        else:
                            size = rect["size"]
                            position = rect["position"]

                            self.draw_rect(
                                canvas, size,
                                position,
                                color, width)

                    else:
                        self.draw_rect(
                            canvas, rect.size,
                            rect.position,
                            color, width)

    @staticmethod
    def draw_rect(canvas, size, position, color, width):
        image = RectGraphics.get_rect_image(
            size, color, width)

        canvas.blit(image, position)

    @staticmethod
    def draw_circle(canvas, radius, position, color, width):
        image = RectGraphics.get_circle_image(
            radius, color, width)
        w, h = image.get_size()
        w /= 2
        h /= 2
        px, py = position
        px -= w
        py -= h

        canvas.blit(image, (px, py))

    @staticmethod
    def get_item_rect(item):
        return item.rect

    @staticmethod
    def get_animation_rect(item, rect_name):
        return item.get_animation_object(rect_name)

    @staticmethod
    def get_hitboxes(item):
        hitboxes = item.animation_machine.get_hitboxes()
        if not hitboxes:
            return []

        else:
            return hitboxes


class DrawVectorLayer(DrawRectLayer):
    def __init__(self, name):
        super(DrawVectorLayer, self).__init__(name)

        self.get_vector_function = None
        self.vector_args = []

    def set_vector_function(self, *args):
        method_name = args[0]
        if len(args) > 1:
            args = args[1:]
        else:
            args = []

        self.get_vector_function = getattr(self, method_name)
        self.vector_args = args

    def draw_items(self, canvas):
        color = self.draw_color
        width = self.draw_width
        get_vectors = self.get_vector_function

        if get_vectors:
            for g in self.groups:

                for item in g:
                    v = get_vectors(item)

                    if not type(v) is list:
                        v = [v]

                    for vector, point in v:
                        image = VectorGraphics.get_vector_image(
                            vector, color, width)

                        canvas.blit(image, point)

    def get_item_velocity(self, item):
        v = item.get_velocity().get_copy(scale=1)

        return v, v.get_draw_point(
            item.position, self.draw_width)

    def get_position_vector(self, item, origin=(0, 0)):
        ox, oy = origin
        px, py = item.position
        dx = px - ox
        dy = py - oy
        v = Vector("{} position".format(item.name),
                   dx, dy)

        return v, v.get_draw_point(origin, self.draw_width)

    def get_region_walls(self, item):
        walls = []
        for w in item.walls:
            point = w.get_draw_point(
                w.origin, self.draw_width)
            walls.append((w, point))

        return walls


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


