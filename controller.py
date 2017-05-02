from classes import CacheList
from input_manager import ButtonMappingKey, ButtonMappingButton, ButtonMappingAxis, ButtonMappingHat
from resources import load_resource
from zs_constants import CONTROLLER_FRAME_DEPTH as SIZE
from zs_constants import INIT_DELAY, HELD_DELAY, UDLR


#
# Virtual controller / input device objects
#

class Controller:
    """
    The Controller object represents a virtual blueprint for a set of input devices
    that will be used for a given game environment. It has a list of input device objects
    and a mapping dictionary that pairs each device with a mapping object that produces the
    input value for a given frame. All of that data is stored in a frame cache by the controller
    object.
    """
    def __init__(self, name):
        self.name = name
        self.frames = CacheList(SIZE)

        self.devices = []
        self.mappings = {}
        self.commands = {}

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    # returns list index for a given device name
    def get_device_index(self, name):
        for d in self.devices:
            if d.name == name:
                return self.devices.index(d)

    # returns device object for a given device name
    def get_device(self, name):
        return self.devices[
            self.get_device_index(name)
        ]

    # returns a frame cache with data for a given device
    def get_device_frames(self, name):
        output = []
        i = self.get_device_index(name)

        for frame in self.frames:
            output.append(frame[i])

        return output

    # add a device / input mapping to the controller object
    def add_device(self, device, mapping):
        self.mappings[device.name] = mapping
        self.devices.append(device)

        if type(device) is Dpad:
            # a Dpad input device is made up of four button devices

            buttons = device.make_d_buttons()
            for i in range(4):
                self.add_device(buttons[i], mapping[i])

    def get_command_frames(self, *device_names):
        device_frames = [self.get_device_frames(n) for n in device_names]
        frames = tuple(zip(*device_frames))

        return frames

    def check_command(self, name):
        return self.commands[name].active

    def add_command_input(self, name, d):
        steps = [Step.get_step_from_key(k) for k in d["steps"]]
        devices = d["devices"]
        window = d.get("window", 1)

        self.commands[name] = Command(
            name, steps, devices, window)

    # update frame input data and call device update methods
    def update(self):
        self.update_frames()

        for d in self.devices:
            d.update()

        for command in self.commands.values():
            frames = self.get_command_frames(*command.devices)
            command.update(frames[-1])

    # append frame data to frame cache object
    def update_frames(self):
        frame = []

        for d in self.devices:
            m = self.mappings[d.name]

            frame.append(
                d.get_input(m)
            )

        self.frames.append(frame)


class InputDevice:
    """
    This abstract superclass defines the main methods of the input device object.
    Each device is paired with a controller object which is used to access the frame cache, and
    some devices have additional attributes that can be altered by the update method based on this
    data. Each device also defines a get_input method for producing frame data.
    """
    def __init__(self, name, controller):
        self.name = name
        self.default = None
        self.controller = controller

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    # get frame cache for this device
    def get_frames(self):
        return self.controller.get_device_frames(self.name)

    # get most recent value from frame cache
    def get_value(self):
        if self.get_frames():
            return self.get_frames()[-1]

        else:
            return self.default

    def update(self):
        pass

    @staticmethod
    def get_input(mapping):
        return int(mapping.is_pressed())


class Button(InputDevice):
    """
    A Button object corresponds to a single button input device. This class
    defines a number of extra attributes and methods that can make controller
    interfacing more useful, such as a negative_edge check method and a check
    method with a built in modular ignore-frame dampener for continuous button
    presses.
    Button objects have a 'held' attribute that records the number of frames the
    button has been continuously held.
    """
    def __init__(self, name, controller):
        super(Button, self).__init__(name, controller)

        self.init_delay = INIT_DELAY
        self.held_delay = HELD_DELAY
        self.held = 0
        self.default = 0

        self.lifted = False

    # ignore / check give a method for getting discrete input intervals from a
    # continuous button push.
    # See zs_constants.py to adjust INIT_DELAY and HELD_DELAY values
    @property
    def ignore(self):
        ignore = False
        h, i_delay, h_delay = (self.held,
                               self.init_delay,
                               self.held_delay)

        if 1 < h < i_delay:
            ignore = True
        elif h >= i_delay:
            if (h - i_delay) % h_delay != 0:
                ignore = True

        return ignore

    def check(self):
        if self.lifted:
            return self.held and not self.ignore

    # negative_edge returns True if a button was pushed the last frame and has just
    # been released. It returns False in all other cases.
    def negative_edge(self):
        frames = self.get_frames()
        current, last = frames[-1], frames[-2]

        return last and not current

    # FRAME DATA:
    # 0: button not pressed
    # 1: button pressed
    @staticmethod
    def get_input(mapping):
        return int(mapping.is_pressed())

    def update(self):
        if not self.lifted:
            self.lifted = 0 in self.get_frames()

        if self.get_value():
            self.held += 1
        else:
            self.held = 0


class Dpad(InputDevice):
    """
    A Dpad object represents an input device that can input 8 discrete directions through
    a combination of four individual buttons, one for up, down, left, and right.
    The 'get_dominant' method is used by the 'check' method to set the 'ignore' flag based
    on the frame interval of whichever Dpad button has been held the longest.
    Dpad objects have a 'last_direction' attribute that defaults to right (1, 0).
    """
    def __init__(self, name, controller):
        super(Dpad, self).__init__(name, controller)
        self.last_direction = (1, 0)
        self.default = (0, 0)

    def get_d_button(self, direction):
        return self.controller.get_device(
            self.name + "_" + direction
        )

    def make_d_buttons(self):
        buttons = []

        for direction in UDLR:
            name = self.name + "_" + direction
            buttons.append(
                Button(name, self.controller)
            )

        return buttons

    @property
    def up(self):
        return self.get_d_button("up")

    @property
    def down(self):
        return self.get_d_button("down")

    @property
    def left(self):
        return self.get_d_button("left")

    @property
    def right(self):
        return self.get_d_button("right")

    @property
    def buttons(self):
        return [
            self.up,
            self.down,
            self.left,
            self.right
        ]

    @property
    def held(self):
        return self.get_dominant().held

    # returns the same thing as 'get_value'
    def get_direction(self):
        return self.get_value()

    # returns the direction button that has been held for the most frames
    def get_dominant(self):
        u, d, l, r = self.buttons

        dominant = sorted([u, d, l, r], key=lambda b: b.held * -1)[0]

        return dominant

    def check(self):
        return self.get_dominant().check()

    # FRAME DATA:
    # 0, 0: neutral
    # +x, +y: right pushed / down pushed
    # -x, -y: left pushed / up pushed
    @staticmethod
    def get_input(mappings):
        u, d, l, r = [m.is_pressed() for m in mappings]

        x, y = 0, 0
        x -= int(l)
        x += int(r)
        y += int(d)
        y -= int(u)

        return x, y

    def update(self):
        x, y = self.get_value()

        if (x, y) != (0, 0):
            self.last_direction = x, y


class Command:
    def __init__(self, name, steps, device_names, frame_window=0):
        self.name = name
        self.steps = steps
        if not frame_window:
            frame_window = sum([step.frame_window for step in steps])
        self.frame_window = frame_window
        self.frames = CacheList(frame_window)
        self.devices = device_names
        self.active = False

    def check(self):
        frames = self.frames
        l = len(frames)
        i = 0
        for step in self.steps:
            sub_slice = frames[i:l]
            j = step.check(sub_slice)
            step.last = j
            i += j
            if j == 0:
                return False

        return True

    def update(self, frame):
        self.frames.append(frame)
        c = self.check()
        self.active = c

        if c:
            self.frames.clear()

    def __repr__(self):
        return self.name


class Step:
    # condition: check_func
    # check_func: function(frame) => Bool

    def __init__(self, name, conditions, frame_window=1):
        self.name = name
        self.conditions = conditions
        self.frame_window = frame_window
        self.last = 0

    def get_matrix(self, frames):
        frame_matrix = []
        conditions = self.conditions

        for con in conditions:
            check = con
            row = [check(frame) for frame in frames]
            frame_matrix.append(row)

        return frame_matrix

    def get_sub_matrix(self, frame_matrix, i):
        conditions = self.conditions
        fw = self.frame_window
        sub_matrix = []

        for con in conditions:
            row_i = conditions.index(con)
            row = frame_matrix[row_i][i:i + fw]
            sub_matrix.append(row)

        return sub_matrix

    def check(self, frames):
        frame_matrix = self.get_matrix(frames)
        fw = self.frame_window
        fl = len(frames)

        for i in range((fl - fw) + 1):
            sub_matrix = self.get_sub_matrix(frame_matrix, i)
            truth = all([any(row) for row in sub_matrix])

            if truth:
                return i + 1
        return 0

    @staticmethod
    def get_step_from_key(key):
        conditions, window = STEP_DICT[key]

        return Step(key, conditions, window)

    def __repr__(self):
        d, fw = self.name, self.frame_window

        return "{}, frame window: {}".format(d, fw)

STEP_DICT = {
    "neutral": ([lambda f: f[0] == (0, 0)], 1),
    "up": ([lambda f: f[0][1] == -1], 1),
    "left": ([lambda f: f[0][0] == -1], 1),
    "right": ([lambda f: f[0][0] == 1], 1)
}

#
# USB device / Keyboard mapping and input manager
#


#
# methods for loading a controller object from a cfg formatted text stream
# or json formatted dictionary
#

DEVICES_DICT = {
    "button": Button,
    "dpad": Dpad,
    "button_map_key": ButtonMappingKey,
    "button_map_button": ButtonMappingButton,
    "button_map_axis": ButtonMappingAxis,
    "button_map_hat": ButtonMappingHat
}


# return a controller object from a cfg formatted file
def load_controller(file_name):
    devices = load_resource(file_name)["devices"]

    return make_controller(
        file_name, devices)


# return a controller object from a json formatted devices dict
def make_controller(name, devices):
    # print_dict(devices)
    controller = Controller(name)

    try:
        for name in devices:
            d = devices[name]
            cls = get_device_class(d)
            mapping = get_mapping(d)

            device = cls(name, controller)
            controller.add_device(
                device, mapping
            )

        return controller

    except IndexError:
        raise IOError("Unable to build controller " + name)
    except AssertionError:
        raise IOError("Unable to build controller " + name)


def get_device_class(d):
    return DEVICES_DICT[d["class"]]


def get_mapping(d):
    def get_m(c, a):
        return DEVICES_DICT[c](*a)

    if d["class"] == "button":
        cls = d["mapping"][0]
        args = d["mapping"][1:]
        return get_m(cls, args)

    if d["class"] == "dpad":
        mappings = []
        for direction in UDLR:
            cls = d[direction][0]
            args = d[direction][1:]

            mappings.append(
                get_m(cls, args)
            )

        return mappings
