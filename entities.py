from classes import Clock, MessageLogger
from controller import load_controller, make_controller
from events import EventHandler
from geometry import Rect, Wall
from graphics import Graphics, ImageGraphics, TextGraphics
from resources import load_resource, load_style, DEFAULT_STYLE
from zs_constants import SCREEN_SIZE, SOUND_EXT, SELECTED_COLOR, UNSELECTED_COLOR, DYING_TIME


class Entity:
    INIT_ORDER = ["model", "style", "position", "size", "graphics"]

    def __init__(self, name):
        self.name = name
        self.model = {}

        self._log = MessageLogger()
        self.log = self._log.log
        self.get_message = self._log.get_message
        self.get_log = self._log.get_log

        self.clock = Clock(name + " clock")
        self.rect = Rect((1, 1), (0, 0))
        self.controllers = []

        self.control_freeze = False
        self.visible = True
        self._graphics = None
        self._style = {}
        self.sounds = {}

        self.event = None
        self.event_handler = EventHandler(self)
        self.handle_event = self.event_handler.handle_event

        self.queue_events(
            {"name": "on_spawn"}
        )

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    def queue_events(self, *events):
        self.event_handler.queue_events(*events)

    def add_listener(self, event_name, response):
        if "target" in response:
            target = response["target"]
        else:
            target = self

        l = {
            "name": event_name,
            "target": target,
            "response": response
        }

        self.event_handler.listeners.append(l)

    def update(self):
        for m in self.get_update_methods():
            m()

    def get_update_methods(self):
        um = [
            self.clock.tick
        ]

        if self.controller:
            um.append(self.controller.update)

        if self.graphics:
            um.append(self.graphics.update)

        return um

    def move(self, dxdy):
        self.rect.move(dxdy)

    def kill(self):
        self.control_freeze = True
        dying = {
            "name": "on_dying",
            "duration": DYING_TIME,
        }
        self.queue_events(dying, "on_death")

    @property
    def graphics(self):
        return self._graphics

    @graphics.setter
    def graphics(self, value):
        if isinstance(value, Graphics):
            self._graphics = value

        else:
            self.set_graphics(value)

    @property
    def controller(self):
        if self.controllers:
            return self.controllers[0]

    @property
    def image(self):
        if self.graphics:
            return self.graphics.get_image()

        else:
            return False

    @property
    def draw_point(self):
        return self.position

    @property
    def position(self):
        return self.get_position()

    @position.setter
    def position(self, value):
        x, y = value
        self.set_position(x, y)

    def get_position(self):
        return self.rect.position

    def set_position(self, x, y):
        self.rect.position = x, y

        self.handle_event("on_change_position")

    @property
    def size(self):
        return self.get_size()

    @size.setter
    def size(self, value):
        w, h = value
        self.set_size(w, h)

    def get_size(self):
        return self.rect.size

    def set_size(self, w, h):
        self.rect.size = w, h

        self.handle_event("on_change_size")

    @property
    def style(self):
        if not self._style:
            self._style = DEFAULT_STYLE.copy()

        return self._style

    @style.setter
    def style(self, value):
        self.set_style(value)

    def set_style(self, style):
        if type(style) is dict:
            self.style.update(style)

        if type(style) is str:
            self._style = load_style(style)

        if self.graphics:
            self.graphics.reset_image()

    def set_graphics(self, graphics, *args, **kwargs):
        self._graphics = graphics(self, *args, **kwargs)

        self.handle_event("on_change_size")

    def set_resources(self, *dict_names):
        for name in dict_names:
            rd = load_resource("resource_dicts")[name]

            for key in rd:
                file_name = rd[key]
                self.add_resource(key, file_name)

    def add_resource(self, key, file_name):
        item = load_resource(file_name)
        ext = file_name.split(".")[-1]

        if ext in SOUND_EXT:
            self.sounds[key] = item

    def set_controller(self, arg, clear=True):
        if type(arg) is str:
            cont = load_controller(arg)

        else:
            name = arg.pop("name")
            cont = make_controller(name, arg)

        if not clear:
            self.controllers.append(cont)

        else:
            self.controllers = [cont]

    def set_controllers(self, controllers):
        for c in controllers:
            self.set_controller(c.name, clear=False)

    def set_controller_index(self, layer, index):
        file_name = layer.controllers[index].name

        self.set_controller(file_name)

    def set_command_inputs(self, *commands):
        for name in commands:
            c = load_resource("command_inputs")[name]

            for controller in self.controllers:
                controller.add_command_input(name, c)

    def set_event_passers(self, target, *event_names):
        for name in event_names:
            l = {
                "name": name,
                "target": target
            }

            self.event_handler.listeners.append(l)

    def set_event(self, event):
        self.event = event.copy()

    def set_model(self, d, update=False):
        if not update:
            self.model = d

        else:
            self.model.update(d)


class Layer(Entity):
    def __init__(self, name):
        super(Layer, self).__init__(name)
        self.size = SCREEN_SIZE

        self.groups = []
        self.sub_layers = []
        self.paused = False

    def main(self, screen):
        self.update()
        self.draw(screen)

    def set_groups(self, *groups):
        self.groups = groups

    def set_parent_layer(self, layer):
        layer.sub_layers.append(self)

    def draw(self, screen):
        # PYGAME CHOKE POINT

        sub_rect = self.rect.clip(
            screen.get_rect())

        try:
            canvas = screen.subsurface(sub_rect)
        except ValueError:      # if the layer's area is entirely outside of the screen's
            return              # area, it doesn't get drawn

        if self.graphics:
            canvas.blit(self.graphics.get_image(), (0, 0))

        self.draw_items(canvas)
        self.draw_sub_layers(canvas)

    def draw_sub_layers(self, canvas):
        for layer in self.sub_layers:
            if layer.visible:
                layer.draw(canvas)

    def draw_items(self, canvas):
        # Draw sprites / effects

        for group in self.groups:
            for item in group:
                if item.graphics and item.image and item.visible:
                    canvas.blit(
                        item.image, item.draw_point
                    )

    def update_sub_layers(self):
        if not self.paused:
            for layer in self.sub_layers:
                layer.update()

    def update_items(self):
        if not self.paused:
            for g in self.groups:

                for item in g:
                    item.update()

    def get_update_methods(self):
        um = super(Layer, self).get_update_methods()

        um += [
            self.update_items,
            self.update_sub_layers
        ]

        return um


class Sprite(Entity):
    def __init__(self, name):
        super(Sprite, self).__init__(name)

        self.selectable = False
        self.groups = []
        self.controller_interface = ControllerInterface(self)

        self._value = None

    def set_name(self, name):
        self.name = name

    def get_value(self):
        val = self._value
        if callable(val):
            return val()

        else:
            return val

    def set_value(self, value):
        self._value = value

    def get_text(self):
        if self.graphics:
            return getattr(self.graphics, "text", self.name)

    def set_text(self, text):
        if not self._value:
            self._value = text
        self.set_graphics(TextGraphics, text)

    def get_size(self):
        if self.graphics:
            return self.image.get_size()

        else:
            return super(Sprite, self).get_size()

    def set_image(self, file_name):
        self.set_graphics(ImageGraphics, file_name)

    def set_group(self, group):
        group.add_item(self)

    def set_controller_interface(self, *method_names):
        self.controller_interface.set_methods(*method_names)

    def get_update_methods(self):
        um = super(Sprite, self).get_update_methods()

        um += [self.controller_interface.update]

        return um

    def on_select(self):
        self.style = {"font_color": SELECTED_COLOR}

    def on_deselect(self):
        self.style = {"font_color": UNSELECTED_COLOR}

    def on_dying(self):
        timer = self.event["timer"]
        graphics = self.graphics

        if graphics and hasattr(graphics, "dying_graphics"):
            graphics.dying_graphics(timer)

    def on_death(self):
        for g in self.groups:
            g.remove_item(self)

    def on_freeze_control(self):
        self.control_freeze = True

    def on_enable_control(self):
        self.control_freeze = False

    def on_give_control(self):
        event = self.event

        sprite = event["sprite"]

        if sprite.control_freeze:
            sprite.control_freeze = False
        sprite.set_controller(
            self.controller.name
        )

        if "controller_interface" in event:
            sprite.set_controller_interface(
                *event["controller_interface"]
            )

        if event.get("control_freeze", False):
            self.control_freeze = True


class ControllerInterface:
    def __init__(self, entity):
        self.entity = entity
        self.control_methods = {}
        self.paused = []

    def __repr__(self):
        return "Controller Interface object for {}".format(self.entity)

    def set_methods(self, *method_names):
        methods = load_resource("control_methods")

        for name in method_names:
            self.add_method(name, methods[name])

    def add_method(self, name, d):
        if "method" in d:
            method_name = d.pop("method")
        else:
            method_name = name

        m = getattr(self, method_name)

        self.control_methods[name] = m, d

    def update(self):
        cm = self.control_methods

        if not self.entity.control_freeze:
            for name in cm:
                if name not in self.paused:
                    m, d = cm[name]

                    test = m(**d)

                    # if test:
                    #     print(self, name)

    #
    # CONTROL METHODS
    #

    def movement(self, device_name="", speed=0):
        sprite = self.entity
        dpad = sprite.controller.get_device(
            device_name)

        x, y = dpad.get_direction()
        x *= speed
        y *= speed

        test = x or y

        if test:
            sprite.move((x, y))

        return test

    def move_vector(self, speed=0):
        sprite = self.entity
        controller = sprite.controller
        dpad = controller.get_device("Dpad")
        a, b = controller.get_device("A"), controller.get_device("B")

        x, y = dpad.get_direction()
        x *= speed
        y *= speed

        test = x or y

        if test:
            vector = sprite.vector
            if not (a.held or b.held):
                sprite.move((x, y))

            if a.held:
                i, j = vector.get_value()
                i += x
                j += y
                vector.set_value(i, j)

            if b.held:
                angle = .005 * x
                vector.rotate(angle)

            sprite.reset_vector()

    def activate(self):
        sprite = self.entity
        device_names = sprite.activate_buttons

        return self.handle_event(device_names, "on_activate")

    def handle_event(self, device_names=(), event=None):
        sprite = self.entity

        if sprite.controller:
            test = self.check_buttons(*device_names)

            if test:
                sprite.queue_events(event)

            return test

    def check_buttons(self, *device_names):
        sprite = self.entity
        buttons = []

        for device_name in device_names:
            buttons.append(
                sprite.controller.get_device(
                    device_name)
            )

        return any(
            [b.check() for b in buttons]
        )

    def move_pointer(self, device_name=""):
        sprite = self.entity
        if sprite.controller:
            dpad = sprite.controller.get_device(
                device_name)

            x, y = dpad.get_direction()

            test = (x or y) and dpad.check()

            if test:
                sprite.move_pointer(x, y)

            return test

    def play_sound(self, device_names=(), file_name="", key=""):
        sprite = self.entity
        if file_name:
            sound = load_resource(file_name)
        else:
            sound = sprite.sounds[key]

        if ControllerInterface.check_buttons(
                sprite, *device_names):
            sound.stop()
            sound.play()

    #
    # STATE TRANSITION METHODS
    #

    def press_direction(self):
        sprite = self.entity
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")

            dp = dpad.held

            return dp

    def attack_button(self):
        sprite = self.entity
        if sprite.controller:
            attack = sprite.controller.get_device("A")

            if attack.lifted:
                return attack.held == 1


class ModelManager:
    def __init__(self, entity):
        self.watches = {}
        self.linked_values = {}
        self.linked_objects = {}

        self.entity = entity

    @property
    def model(self):
        return self.entity.model

    def add_get_value_func(self, value_name, get_value):
        self.linked_values[value_name] = get_value

    def add_set_value_func(self, value_name, set_value):
        self.linked_objects[value_name] = set_value

    def check_value_change(self, value_name):
        # value = self.linked_values[value_name]
        value = self.model[value_name]

        if value_name in self.watches:
            change = not self.watches[value_name] == value

        else:
            change = True

        return change

    def set_values_from_table(self, table):
        self.model.update(table)

    def link_value(self, value_name, obj, get_value):
        args = []

        if type(get_value) is list:
            args = get_value[1:]
            get_value = get_value[0]

        if obj:
            def get_func():
                return getattr(obj, get_value)(*args)
        else:
            def get_func():
                return get_value(*args)

        self.add_get_value_func(
            value_name, get_func)

    def link_object(self, value_name, obj, set_value):
        if obj:
            set_value = getattr(obj, set_value)
        else:
            set_value = set_value

        self.add_set_value_func(
            value_name, set_value)

        self.watches[value_name] = self.model.get(value_name)

    def update(self):
        value_dict = self.linked_values
        obj_dict = self.linked_objects

        # update linked values

        for name in value_dict:
            get_value = value_dict[name]
            self.model[name] = get_value()

        # update linked objects

        for name in obj_dict:
            if self.check_value_change(name):
                value = self.model[name]
                self.watches[name] = value

                set_value = obj_dict[name]
                set_value(value)


class Region(Sprite):
    def __init__(self, name):
        super(Region, self).__init__(name)

        self.walls = []

    def set_walls(self, *walls):
        for w in walls:
            if type(w) is str:
                w = load_resource("walls")[w]

            wall = Wall(w["name"], w["origin"], w["end"])
            wall.log = self.log

            self.walls.append(
                wall
            )

    def set_group(self, group):
        group.add_item(self)

    def test_sprite_collision(self, sprite):
        collisions = []
        test = sprite.physics_interface.test_wall_collision

        for wall in self.walls:
            collision = test(wall, sprite)

            if collision:
                collisions.append((wall, collision))

        return collisions

    @staticmethod
    def handle_sprite_collision(sprite, collisions):
        handle = sprite.physics_interface.smooth_wall_collision

        for c in collisions:
            wall, point = c

            handle(wall, sprite, point)
