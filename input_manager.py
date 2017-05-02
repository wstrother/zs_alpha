import pygame


'''
The following "Mapping" classes are basically just wrapper objects for interfacing
with the Pygame keyboard / USB joystick modules. They should each provide a single method
for returning a data argument for the Controller / Device objects 'get_value' methods.
'''

pygame.init()


class ButtonMappingKey:
    def __init__(self, id_num):
        if type(id_num) is str:
            id_num = self.get_id(id_num)

        self.id_num = id_num

    def __repr__(self):
        return "Button Map Key: {}".format(self.get_key_name())

    def get_args(self):
        return ["button_map_key", self.get_key_name()]

    def is_pressed(self):
        return pygame.key.get_pressed()[self.id_num]

    def get_key_name(self):
        return pygame.key.name(self.id_num)

    @staticmethod
    def get_id(key_string):
        if len(key_string) > 1:
            key = "K_" + key_string.upper()
        else:
            key = "K_" + key_string

        return pygame.__dict__[key]


class ButtonMappingButton(ButtonMappingKey):
    def __init__(self, id_num, joy_device_name, joy_id):
        super(ButtonMappingButton, self).__init__(id_num)
        self.joy_device = InputManager.INPUT_DEVICES[joy_id]

        assert self.joy_device.get_name() == joy_device_name

    def get_args(self):
        return ["button_map_button", self.id_num,
                self.joy_device.get_name(),
                self.joy_device.get_id()]

    def is_pressed(self):
        return self.joy_device.get_button(self.id_num)


class ButtonMappingAxis(ButtonMappingButton):
    DEAD_ZONE = .1

    def __init__(self, id_num, joy_device_name, joy_id, sign):
        super(ButtonMappingAxis, self).__init__(
            id_num, joy_device_name, joy_id)
        self.dead_zone = ButtonMappingAxis.DEAD_ZONE
        self.sign = sign

    def get_args(self):
        return ["button_map_axis", self.id_num,
                self.joy_device.get_name(),
                self.joy_device.get_id(),
                self.sign]

    def is_pressed(self):
        axis = self.joy_device.get_axis(self.id_num)

        return axis * self.sign > self.dead_zone


class ButtonMappingHat(ButtonMappingButton):
    def __init__(self, id_num, joy_device_name, joy_id, position, axis):
        super(ButtonMappingHat, self).__init__(id_num, joy_device_name, joy_id)
        self.position = position
        self.axis = axis

    def get_args(self):
        return ["button_map_hat", self.id_num,
                self.joy_device.get_name(),
                self.joy_device.get_id(),
                self.position,
                self.axis]

    def is_pressed(self):
        hat = self.joy_device.get_hat(self.id_num)
        if self.axis != -1:
            return hat[self.axis] == self.position
        else:
            return hat == self.position


class AxisMapping:
    def __init__(self, id_num, joy_device_name, joy_id, sign):
        self.id_num = id_num
        self.sign = sign
        self.joy_device = InputManager.INPUT_DEVICES[joy_id]

        assert self.joy_device.get_name() == joy_device_name

    def get_args(self):
        return ["axis_mapping", self.id_num,
                self.joy_device.get_name(),
                self.joy_device.get_id(),
                self.sign]

    def get_value(self):
        sign = self.sign

        return self.joy_device.get_axis(self.id_num) * sign


class InputManager:
    STICK_DEAD_ZONE = .1
    AXIS_NEUTRAL = False
    AXIS_MIN = .9
    INPUT_DEVICES = []

    for J in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(J)
        joy.init()
        INPUT_DEVICES.append(joy)

    @staticmethod
    def check_axes():
        axes = []
        for device in InputManager.INPUT_DEVICES:
            for i in range(device.get_numaxes()):
                axes.append(device.get_axis(i))

        if not InputManager.AXIS_NEUTRAL:
            InputManager.AXIS_NEUTRAL = all([axis < .01 for axis in axes])

    @staticmethod
    def get_mapping():
        devices = InputManager.INPUT_DEVICES

        pygame.event.clear()
        while True:
            InputManager.check_axes()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                axis, button, hat, key = (
                    event.type == pygame.JOYAXISMOTION,
                    event.type == pygame.JOYBUTTONDOWN,
                    event.type == pygame.JOYHATMOTION,
                    event.type == pygame.KEYDOWN)

                if key:
                    return ButtonMappingKey(event.key)

                if hasattr(event, "joy"):
                    input_device = devices[event.joy]

                    if axis and abs(event.value) > InputManager.AXIS_MIN:
                        positive = event.value > 0
                        sign = (int(positive) * 2) - 1      # -1 for False, 1 for True

                        if InputManager.AXIS_NEUTRAL:
                            InputManager.AXIS_NEUTRAL = False
                            return ButtonMappingAxis(
                                event.axis, input_device.get_name(),
                                input_device.get_id(), sign)

                    if button:
                        return ButtonMappingButton(
                            event.button,
                            input_device.get_name(),
                            input_device.get_id())

                    if hat:
                        x, y = event.value
                        if x != 0 and y == 0:
                            axis = 0
                            value = event.value[0]
                        elif y != 0 and x == 0:
                            axis = 1
                            value = event.value[1]
                        elif x != 0 and y != 0:
                            axis = -1
                            value = event.value
                        else:
                            break

                        return ButtonMappingHat(
                            event.hat, input_device.get_name(),
                            input_device.get_id(), value, axis)

    @staticmethod
    def get_axis():
        devices = InputManager.INPUT_DEVICES
        if len(devices) == 0:
            raise IOError("No input devices connected")
        sticks = [device.get_numaxes() > 0 for device in devices]
        if not any(sticks):
            raise IOError("No axes detected for connected devices")

        while True:
            InputManager.check_axes()

            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > InputManager.AXIS_MIN:

                    positive = event.value > 0
                    if positive:
                        sign = 1
                    else:
                        sign = -1
                    id_num = event.axis
                    input_device = InputManager.INPUT_DEVICES[event.joy]

                    if InputManager.AXIS_NEUTRAL:
                        InputManager.AXIS_NEUTRAL = False
                        return AxisMapping(
                            id_num, input_device, sign)
