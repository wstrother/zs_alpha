from entities import Layer
from geometry import Rect


import pygame


class CameraLayer(Layer):
    def __init__(self, name):
        self.scale = 1
        self.view_rect = Rect((1, 1), (0, 0))

        super(CameraLayer, self).__init__(name)

        self.target_name = None

        self.track_function = None
        self.scale_function = None

    def get_screen_px(self, world_px):
        wx, wy = world_px

        wx /= self.scale
        wy /= self.scale

        x, y = self.view_rect.topleft

        return wx - x, wy - y

    def get_world_px(self, screen_px):
        sx, sy = screen_px
        sx *= self.scale
        sy *= self.scale

        x, y = self.view_rect.topleft
        sx += x
        sy += y

        return sx, sy

    def get_scale(self):
        return self.scale

    def set_scale(self, value):
        self.scale = value
        self.set_view_rect_size()

    def set_size(self, w, h):
        super(CameraLayer, self).set_size(w, h)
        self.set_view_rect_size()

    def set_view_rect_size(self):
        rect = self.view_rect
        cx, cy = rect.center
        w, h = self.size

        w /= self.scale
        h /= self.scale

        rect.size = w, h
        rect.center = cx, cy

    def set_view_position(self, x, y):
        self.view_rect.position = x, y

    def set_focus(self, fx, fy):
        self.view_rect.center = fx, fy

    def set_tracking_function(self, obj, method_name):
        self.track_function = getattr(obj, method_name)

    def set_scale_function(self, obj, method_name, *args):
        m = getattr(obj, method_name)
        self.scale_function = lambda: m(*args)

    def set_target(self, name):
        self.target_name = name

    def get_view_rect(self):
        return self.view_rect.copy()

    def get_camera_rects(self):
        return [self.get_view_rect()]

    def get_camera_surface(self, screen):
        sub_rect = self.rect.clip(
            screen.get_rect())

        w, h = sub_rect.size
        w /= self.scale
        h /= self.scale

        return pygame.Surface((w, h)).convert()

    def get_camera_offset(self, offset=(0, 0)):
        ox, oy = offset
        vx, vy = self.view_rect.topleft

        ox -= vx
        oy -= vy

        return ox, oy

    def draw(self, screen, offset=(0, 0), draw_point=(0, 0)):
        ox, oy = self.get_camera_offset(offset)

        if self.scale != 1:
            true_canvas = self.get_canvas(screen)
            canvas = self.get_camera_surface(screen)

            if self.graphics and self.visible:
                true_canvas.blit(self.graphics.get_image(), draw_point)

            self.draw_items(canvas, (ox, oy))
            self.draw_sub_layers(canvas, (ox, oy), (ox, oy))

            pygame.transform.scale(
                canvas, true_canvas.get_size(), true_canvas)

        else:
            super(CameraLayer, self).draw(screen, (ox, oy), (ox, oy))

    def draw_items(self, canvas, offset=(0, 0)):
        ox, oy = offset

        def get_height(i):
            ix, iy = i.draw_point
            w, h = i.image.get_size()

            return iy + h

        for g in self.groups:
            items = [i for i in g if (i.graphics and i.image and i.visible)]
            for item in sorted(items, key=get_height):
                x, y = item.draw_point
                x += ox
                y += oy

                canvas.blit(item.image, (x, y))

    def update(self):
        super(CameraLayer, self).update()

        if self.track_function:
            fx, fy = self.track_function()

            self.set_focus(fx, fy)

        if self.scale_function:
            self.set_scale(self.scale_function())

    def on_spawn(self):
        if self.target_name:
            obj = self.model[self.target_name]

            self.set_tracking_function(obj, "get_position")

            if "camera_scale" in obj.meters:
                self.set_scale_function(obj, "get_meter_value", "camera_scale")
