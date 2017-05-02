from os import listdir
from os.path import join

from input_manager import InputManager
from resources import load_resource
from sprites.gui import OptionBlockSprite
from zs_cfg import format_dict, save_cfg
from zs_constants import CFG, DIALOG_POSITION, UDLR


class PauseMenu(OptionBlockSprite):
    def __init__(self, name):
        super(PauseMenu, self).__init__(name)

        self.activate_buttons = ("A",)

    def set_menu(self):
        resume_option = self.get_sprite_from_value("Resume Game")
        resume_option.selectable = True

        self.add_option_response(resume_option, "on_unpause")

        frame_advance = self.get_sprite_from_value("Frame Advance Mode")
        frame_advance.selectable = True

        self.add_option_response(frame_advance, "on_frame_advance")
        self.add_option_response(frame_advance, "on_unpause")

        self.set_members([
            [resume_option],
            [frame_advance]
        ])

    def on_spawn(self):
        super(PauseMenu, self).on_spawn()

        self.set_menu()
        self.set_options("exit")
        x, y = DIALOG_POSITION
        x -= 100
        y -= 100
        self.set_position(x, y)

    def on_unpause(self):
        group = self.groups[0]
        self.kill()

        for item in group:
            item.kill()


class CursorMenu(OptionBlockSprite):
    def set_menu(self, cursor_sprite):
        # MOVE CURSOR

        move_cursor = self.get_sprite_from_value("Move Cursor")
        move_cursor.selectable = True

        self.add_option_response(
            move_cursor, {
                "name": "on_move_cursor",
                "cursor": cursor_sprite
            })

        # EDIT CURSOR POSITION

        edit_cursor = self.get_sprite_from_value("Edit Cursor Position")
        edit_cursor.selectable = True

        self.add_option_response(
            edit_cursor, "on_edit_cursor")

        self.set_members([
            [move_cursor],
            [edit_cursor]
        ])

    def on_move_cursor(self):
        cursor_sprite = self.event["cursor"]
        x, y = cursor_sprite.get_position()
        y -= 100

        on_move_cursor = {
            "name": "on_give_control",
            "sprite": cursor_sprite,
            "controller_interface": ["movement"],
            "position": [x, y]
        }
        self.handle_event(on_move_cursor)

        on_move_cursor_dialog = {
            "name": "on_show_dialog",
            "dialog": "cursor_dialog",
            "body": "Move Cursor with Dpad \nPress return when done",
            "on_death": {
                "name": "on_freeze_control",
                "target": cursor_sprite
            }
        }
        self.handle_event(on_move_cursor_dialog)


class ControllerMenu(OptionBlockSprite):
    def set_menu(self, directory):
        self.set_member_table(
            MenuTools.list_cfg(directory)
        )

        for option in self.options:
            option.set_text(
                MenuTools.file_name_to_header(
                    option.get_text())
            )

            block = EditControllerMenu()  # controller file_name
            block.set_menu(option.get_value())

            self.add_option_response(
                option, MenuTools.load_sub_block(block)
            )


class EditControllerMenu(OptionBlockSprite):
    def __init__(self):
        super(EditControllerMenu, self).__init__("Edit Controller Menu")
        self.set_controller_interface("return")

    def set_menu(self, file_name):
        devices = load_resource(file_name)["devices"]
        self.set_model(devices)

        options = []

        for name in devices:
            options.append(name)

        self.set_member_table(options)

        self.set_header(
            MenuTools.file_name_to_header(file_name)
        )

        for option in self.options:
            name = option.get_text()
            cls = devices[name]["class"]
            on_activate = ""

            if cls == "button":
                on_activate = {
                    "name": "on_map_button",
                    "device_name": name
                }

            if cls == "dpad":
                on_activate = {
                    "name": "on_map_dpad",
                    "device_name": name
                }

            self.add_option_response(
                option, on_activate
            )

        self.set_options("save_controller")

    def on_map_button(self):
        name = self.event["device_name"]

        block = MapButtonBlock(name)
        block.set_body("Press any key or button for {}".format(name))

        block.add_listener("on_death", {
            "name": "on_update_devices",
            "device_name": name,
            "class": "button",
            "block": block,
            "target": self
        })

        map_button_event = {
            "name": "on_change_block",
            "block": block,
            "death": "on_return"
        }

        self.handle_event(map_button_event)

    def on_map_dpad(self):
        name = self.event["device_name"]
        index = self.event.get("dpad_index", 0)

        block = MapButtonBlock(name + UDLR[index])
        block.set_body("Press {} on {}".format(UDLR[index], name))

        block.add_listener("on_death", {
            "name": "on_update_devices",
            "device_name": name,
            "class": "dpad",
            "dpad_index": index,
            "block": block,
            "target": self
        })

        map_dpad_event = {
            "name": "on_change_block",
            "block": block,
            "death": "on_return"
        }

        self.handle_event(map_dpad_event)

    def on_update_devices(self):
        block = self.event["block"]
        name = self.event["device_name"]
        cls = self.event["class"]

        if cls == "button":
            self.model[name]["mapping"] = block.get_value()
            self.update_controller()

        if cls == "dpad":
            index = self.event["dpad_index"]
            self.model[name][UDLR[index]] = block.get_value()

            if index < 3:
                self.queue_events({
                    "name": "on_map_dpad",
                    "device_name": name,
                    "dpad_index": index + 1
                })

            if index == 3:
                self.update_controller()

        format_dict(self.model)

    def update_controller(self):
        file_name = self.controller.name
        devices = self.model.copy()
        devices["name"] = file_name

        self.set_controller(devices)

    def on_save_controller(self):
        controller = self.controllers[
            self.event["index"]
        ]
        path = join(CFG, "controllers", controller.name)
        cfg = {"devices": self.model.copy()}
        # print(format_dict(cfg))
        save_cfg(cfg, path)


class MapButtonBlock(OptionBlockSprite):
    def on_spawn(self):
        super(MapButtonBlock, self).on_spawn()
        self.set_position(*DIALOG_POSITION)

        self.queue_events({
            "name": "on_get_mapping"
        })

    def on_get_mapping(self):
        self.control_freeze = True

        m = InputManager.get_mapping()
        self.set_value(m.get_args())

        self.queue_events("on_return")


class EnvironmentMenu(OptionBlockSprite):
    def set_menu(self, directory):
        self.set_member_table(
            MenuTools.list_cfg(directory)
        )

        for option in self.options:
            option.set_text(
                MenuTools.file_name_to_header(
                    option.get_text())
            )

            self.add_option_response(
                option, MenuTools.load_environment(option)
            )


class MenuTools:
    #
    # GET OPTION METHODS
    #

    @staticmethod
    def file_name_to_header(file_name):
        name = ".".join(file_name.split(".")[:-1])
        name = name.replace("_", " ")

        header = ""
        for word in name.split():
            header += word.capitalize() + " "

        return header[:-1]

    @staticmethod
    def list_cfg(directory=None):
        if directory:
            return listdir(join(CFG, directory))

    @staticmethod
    def load_section(file_name, section):
        return load_resource(file_name)[section]

    #
    # GET EVENT METHODS
    #

    @staticmethod
    def load_environment(o):
        return {
            "name": "on_exit",
            "environment": o.get_value()
        }

    @staticmethod
    def load_sub_block(block):
        return {
            "name": "on_change_block",
            "block": block,
            "death": "on_return"
        }
