import pygame

from resources import get_font, load_resource, DEFAULT_STYLE
from zs_constants import SCREEN_SIZE
from geometry import Rect

# PYGAME CHOKE POINT

pygame.font.init()
BORDER_CORNER_CHOICES = "abcd"
RECT_DRAW_WIDTH = 5
RECT_DRAW_COLOR = 255, 0, 0


class Graphics:
    PRE_RENDERS = {}

    def __init__(self, entity):
        self.entity = entity
        self.image = None

        self.reset_image()

    def update(self):
        pass

    def get_image(self):
        return self.image

    def make_image(self):
        pass

    def reset_image(self):
        self.image = self.make_image()

        if self.entity.rect:
            self.entity.rect.size = self.image.get_size()

    def dying_graphics(self, timer):
        ratio = 1 - timer.get_ratio()
        self.image.set_alpha(255 * ratio)


class ImageGraphics(Graphics):
    def __init__(self, entity, file_name):
        self.file_name = file_name
        super(ImageGraphics, self).__init__(entity)

    def make_image(self):
        image = load_resource(self.file_name)
        self.set_colorkey(image)

        return image

    @staticmethod
    def set_colorkey(img, pixel=(0, 0)):
        # PYGAME CHOKE POINT

        img.set_colorkey(
            img.get_at(pixel)
        )


class TextGraphics(Graphics):
    def __init__(self, entity, text):
        if type(text) not in (str, list):
            text = str(text)
        self.text = text

        super(TextGraphics, self).__init__(entity)

    def make_image(self):
        if self.entity.style:
            style = self.entity.style
        else:
            style = DEFAULT_STYLE

        font_name = style["font_name"]
        size = style["font_size"]
        bold = style.get("bold", False)
        italic = style.get("italic", False)
        color = style["font_color"]
        buffer = style["text_buffer"]
        cutoff = style.get("text_cutoff", None)
        nl = style.get("text_newline", True)

        font = get_font(
            font_name, size, bold, italic)

        image = self.make_text_image(
            self.text, font, color, buffer,
            cutoff=cutoff, nl=nl)

        return image

    @staticmethod
    def get_text(text, cutoff, nl):
        if type(text) == str:
            text = [text]

        for i in range(len(text)):
            line = str(text[i])
            line = line.replace("\t", "    ")
            line = line.replace("\r", "\n")
            if not nl:
                line = line.replace("\n", "")
            text[i] = line

        new_text = []

        for line in text:
            if cutoff:
                new_text += TextGraphics.format_text(
                    line, cutoff)
            else:
                if nl:
                    new_text += line.split("\n")
                else:
                    new_text += [line]

        if not new_text:
            new_text = [" "]

        return new_text

    @staticmethod
    def make_text_image(text, font, color, buffer,
                        cutoff=0, nl=True):
        text = TextGraphics.get_text(
            text, cutoff, nl)

        line_images = []
        for line in text:
            line_images.append(
                font.render(line, 1, color))

        widest = sorted(line_images, key=lambda l: -1 * l.get_size()[0])[0]
        line_height = (line_images[0].get_size()[1] + buffer)
        w, h = widest.get_size()[0], (line_height * len(line_images)) - buffer

        sprite_image = pygame.Surface(
            (w, h), pygame.SRCALPHA, 32)

        for i in range(len(line_images)):
            image = line_images[i]
            y = line_height * i
            sprite_image.blit(image, (0, y))

        return sprite_image

    @staticmethod
    def format_text(text, cutoff):
        f_text = []
        last_cut = 0

        for i in range(len(text)):
            char = text[i]
            done = False

            if char == "\n" and i - last_cut > 0:
                f_text.append(text[last_cut:i])
                last_cut = i + 1
                done = True

            if i == len(text) - 1:
                f_text.append(text[last_cut:])
                done = True

            if i - last_cut >= cutoff and not done:
                if char == " ":
                    f_text.append(text[last_cut:i])
                    last_cut = i + 1
                else:
                    search = True
                    x = i
                    while search:
                        x -= 1
                        if text[x] == " ":
                            next_line = text[last_cut:x]
                            last_cut = x + 1
                            f_text.append(next_line)
                            search = False
                        else:
                            if x <= last_cut:
                                next_line = text[last_cut:i]
                                last_cut = i
                                f_text.append(next_line)
                                search = False

        return f_text


class RectGraphics(Graphics):
    def make_image(self):
        entity = self.entity
        color = entity.style.get(
            "draw_color", RECT_DRAW_COLOR)

        return self.get_rect_image(
            entity.size, color, RECT_DRAW_WIDTH)

    @staticmethod
    def get_rect_image(size, color, draw_width):
        # PYGAME CHOKE POINT

        rect = pygame.Rect((0, 0), size)
        image = pygame.Surface(
            size, pygame.SRCALPHA, 32)
        pygame.draw.rect(
            image, color, rect, draw_width)

        return image

    @staticmethod
    def get_circle_image(radius, color, draw_width):
        # PYGAME CHOKE POINT

        size = 2 * radius, 2 * radius
        position = radius, radius

        image = pygame.Surface(
            size, pygame.SRCALPHA, 32)

        pygame.draw.circle(
            image, color, position,
            radius, draw_width)

        return image


class VectorGraphics(Graphics):
    def make_image(self):
        vector = self.entity.vector
        color = self.entity.draw_color
        width = self.entity.draw_width

        return self.get_vector_image(
            vector, color, width)

    @staticmethod
    def get_vector_image(vector, color, width, scale=1):
        w, h = vector.get_value()
        w = abs(w)
        w *= scale
        h = abs(h)
        h *= scale
        inner = Rect((w, h), (width, width))

        w += width * 2
        h += width * 2
        outer = Rect((w, h), (0, 0))

        # PYGAME CHOKE POINT
        image = pygame.Surface(outer.size, pygame.SRCALPHA, 32)

        q = vector.get_quadrant()
        angle = vector.get_angle()

        if q == 1 or q == 3:
            if not (angle == 0 or angle == .5):
                points = inner.bottomleft, inner.topright
            else:
                points = inner.midleft, inner.midright

            if q == 1:
                end = points[1]

            else:
                end = points[0]

        else:
            if not (angle == .25 or angle == .75):
                points = inner.bottomright, inner.topleft
            else:
                points = inner.midbottom, inner.midtop

            if q == 2:
                end = points[1]

            else:
                end = points[0]

        p1, p2 = points
        p1 = int(p1[0]), int(p1[1])
        p2 = int(p2[0]), int(p2[1])
        pygame.draw.line(image, color, p1, p2, width)
        end = int(end[0]), int(end[1])
        pygame.draw.circle(image, color, end, width, 0)

        return image


class ContainerGraphics(Graphics):
    def __init__(self, entity):
        super(ContainerGraphics, self).__init__(entity)

    def make_image(self, bg_color=False):
        entity = self.entity
        size = entity.rect.size

        if entity.style:
            style = entity.style
        else:
            style = DEFAULT_STYLE

        if not bg_color:
            # BG COLOR
            if style["bg_color"]:
                bg_color = style["bg_color"]
            else:
                bg_color = 0, 0, 0

        image = self.make_color_image(
            size, bg_color)

        # BG TILE IMAGE
        if style["bg_image"]:
            image = self.tile(
                style["bg_image"], image)

        # BORDERS
        if style["border"]:
            border_images = style["border_images"]
            sides = style["border_sides"]
            corners = style["border_corners"]

            image = self.make_border_image(
                border_images, image, sides, corners
            )

        # BORDER ALPHA TRIM
        if style["alpha_color"]:
            image = self.convert_colorkey(
                image, (255, 0, 0)
            )

        return image

    @staticmethod
    def tile(image_name, surface):
        # PYGAME CHOKE POINT

        if image_name not in Graphics.PRE_RENDERS:
            bg_image = load_resource(image_name)
            sx, sy = SCREEN_SIZE    # pre render the tiled background
            sx *= 2                 # to the size of a full screen
            sy *= 2
            pr_surface = pygame.Surface(
                (sx, sy), pygame.SRCALPHA, 32)

            w, h = pr_surface.get_size()
            img_w, img_h = bg_image.get_size()

            for x in range(0, w + img_w, img_w):
                for y in range(0, h + img_h, img_h):
                    pr_surface.blit(bg_image, (x, y))

            Graphics.PRE_RENDERS[image_name] = pr_surface

        full_bg = Graphics.PRE_RENDERS[image_name]      # return a subsection of the full
        #                                               # pre rendered background
        r = surface.get_rect().clip(full_bg.get_rect())
        blit_region = full_bg.subsurface(r)
        surface.blit(blit_region, (0, 0))

        return surface

    @staticmethod
    def make_color_image(size, color):
        # PYGaME CHOKE POINT

        s = pygame.Surface(size).convert()
        if color:
            s.fill(color)
        else:
            s.set_colorkey(s.get_at((0, 0)))

        return s

    @staticmethod
    def convert_colorkey(surface, colorkey):
        surface.set_colorkey(colorkey)
        # new_surface = pygame.Surface(
        #     surface.get_size(), pygame.SRCALPHA, 32)
        # new_surface.blit(surface, (0, 0))
        #
        # return new_surface

        return surface

    @staticmethod
    def make_border_image(border_images, surface, sides, corners):
        h_side_image, v_side_image, corner_image = border_images

        draw_corners = ContainerGraphics.draw_corners
        full_h_side = ContainerGraphics.get_h_side(h_side_image)
        full_v_side = ContainerGraphics.get_v_side(v_side_image)

        w, h = surface.get_size()

        if "l" in sides:
            surface.blit(full_h_side, (0, 0))

        if "r" in sides:
            h_offset = w - full_h_side.get_size()[0]
            surface.blit(pygame.transform.flip(
                full_h_side, True, False), (h_offset, 0))

        if "t" in sides:
            surface.blit(full_v_side, (0, 0))

        if "b" in sides:
            v_offset = h - full_v_side.get_size()[1]
            surface.blit(pygame.transform.flip(
                full_v_side, False, True), (0, v_offset))

        if corners:
            draw_corners(corner_image, surface, corners)

        return surface

    @staticmethod
    def get_h_side(image):
        return ContainerGraphics.get_full_side_image(image, "h")

    @staticmethod
    def get_v_side(image):
        return ContainerGraphics.get_full_side_image(image, "v")

    @staticmethod
    def get_full_side_image(image_name, orientation):
        if image_name not in ContainerGraphics.PRE_RENDERS:
            image = load_resource(image_name)
            iw, ih = image.get_size()

            h, v = "hv"
            size = {h: (iw, SCREEN_SIZE[1]),
                    v: (SCREEN_SIZE[0], iw)}[orientation]
            pr_surface = pygame.Surface(
                size, pygame.SRCALPHA, 32)

            span = {h: range(0, size[1], ih),
                    v: range(0, size[0], iw)}[orientation]

            for i in span:
                position = {h: (0, i),
                            v: (i, 0)}[orientation]
                pr_surface.blit(image, position)

            ContainerGraphics.PRE_RENDERS[image_name] = pr_surface

        return ContainerGraphics.PRE_RENDERS[image_name]

    @staticmethod
    def draw_corners(image_name, surface, corners):
        corner_image = load_resource(image_name)
        w, h = surface.get_size()
        cw, ch = corner_image.get_size()
        a, b, c, d = BORDER_CORNER_CHOICES
        locations = {a: (0, 0),
                     b: (w - cw, 0),
                     c: (0, h - ch),
                     d: (w - cw, h - ch)}

        for corner in corners:
            surface.blit(ContainerGraphics.get_corner(corner_image, corner), locations[corner])

    @staticmethod
    def get_corner(img, string):
        a, b, c, d = BORDER_CORNER_CHOICES
        flip = pygame.transform.flip
        corner = {a: lambda i: i,
                  b: lambda i: flip(i, True, False),
                  c: lambda i: flip(i, False, True),
                  d: lambda i: flip(i, True, True)}[string](img)

        return corner

