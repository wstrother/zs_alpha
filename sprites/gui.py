from classes import MemberTable, CacheList, AverageCache, ChangeCache, Timer
from context_manager import init_item
from entities import Sprite, ModelManager
from graphics import ContainerGraphics, VectorGraphics
from resources import load_resource
from zs_constants import DIALOG_POSITION
from geometry import Vector, Wall

BLOCKS = load_resource("blocks")
OPTIONS = load_resource("options")
EVENTS = load_resource("events")
TABLES = load_resource("tables")
DIALOG_TABLE = TABLES["dialog"]

HUD_FREQUENCY = 12
PRECISION = 3


class GuiMemberTable(MemberTable):
    def adjust_size(self, size, border_size, buffers):
        w, h = size
        border_w, border_h = border_size
        buff_w, buff_h = buffers

        body_w, body_h = self.get_minimum_body_size(buffers)
        full_w, full_h = (
            body_w + ((border_w + buff_w) * 2),
            body_h + ((border_h + buff_h) * 2))

        if w < full_w:
            w = full_w
        if h < full_h:
            h = full_h

        return w, h

    def get_minimum_body_size(self, buffers):
        members = self.members
        r_widths, r_heights = [], []
        buff_w, buff_h = buffers

        for row in members:
            row_w, row_h = self.get_minimum_row_size(row, buff_w)
            r_widths.append(row_w)
            r_heights.append(row_h)

        try:
            width = sorted(r_widths, key=lambda x: x * -1)[0]
        except IndexError:
            width = 0
        height = sum(r_heights) + ((len(r_heights) - 1) * buff_h)

        return width, height

    @staticmethod
    def get_minimum_row_size(row, buff_w):
        row_w, row_h = 0, 0
        item_widths = []

        for item in row:
            w, h = getattr(item, "size", (0, 0))
            item_widths.append(w)

            if h > row_h:
                row_h = h
        row_w = sum(item_widths) + ((len(row) - 1) * buff_w)

        return row_w, row_h

    def set_member_positions_flow(self, position, size, border_size, buffers, aligns):
        if self.member_list:
            parent_x, parent_y = position
            w, h = size
            align_h, align_v = aligns
            border_w, border_h = border_size
            buff_w, buff_h = buffers

            edge_x, edge_y = border_w + buff_w, border_h + buff_h
            body_w, body_h = w - (edge_x * 2), h - (edge_y * 2)

            def get_cell_size(items):
                ch = body_w / len(items)
                cw = body_h / len(self.members)

                return ch, cw

            i, y_disp = 0, 0
            for row in self.members:
                if row:
                    cell_w, cell_h = get_cell_size(row)

                    row_w, row_h = self.get_minimum_row_size(row, buff_w)

                    j, x_disp = 0, 0
                    for item in row:
                        if item:
                            item_w, item_h = item.size
                            x, y = edge_x, edge_y
                            r_offset = body_w - row_w
                            b_edge = body_h - self.get_minimum_body_size(buffers)[1]

                            x += {
                                "l": x_disp,
                                "c": (j * cell_w) + ((cell_w - item_w) / 2),
                                "r": r_offset + x_disp}[align_h]
                            y += {
                                "t": y_disp,
                                "c": (i * cell_h) + ((cell_h - item_h) / 2),
                                "b": b_edge + y_disp}[align_v]

                            item.position = parent_x + x, parent_y + y
                            x_disp += item_w + buff_w
                        j += 1
                    y_disp += row_h + buff_h
                    i += 1

    @staticmethod
    def get_cell_size(size, num_cells):
        w, h = size

        return w / num_cells, h / num_cells


class ContainerSprite(Sprite):
    def __init__(self, name):
        super(ContainerSprite, self).__init__(name)
        self.INIT_ORDER = ContainerSprite.INIT_ORDER + [
            "member_table", "menu", "body", "header", "options"
        ]

        self.table = GuiMemberTable(name + " table")

    def move(self, dxdy):
        super(ContainerSprite, self).move(dxdy)

        for item in self.table.member_list:
            item.move(dxdy)

    def get_text(self):
        return self.table.str_members(sep="")

    def get_member(self, row, index):
        return self.table.members[row][index]

    def set_position(self, x, y):
        super(ContainerSprite, self).set_position(x, y)

        self.adjust_table()

    def set_size(self, w, h):
        w, h = self.adjust_size(w, h)
        super(ContainerSprite, self).set_size(w, h)

        if self.graphics and self.size != self.rect.size:
            self.graphics.reset_image()

    def adjust_size(self, w, h):
        style = self.style
        border_size = style["border_size"]
        buffers = style["cell_buffer"]

        return self.table.adjust_size(
            (w, h), border_size, buffers
        )

    def fix_size(self):
        w, h = self.size
        self.set_size(w, h)

    def adjust_table(self):
        if self.style["position_style"] == "flow":
            self.fix_size()
            self.set_member_positions()

    def kill_members(self):
        for item in self.table.member_list:
            item.kill()

    def set_graphics(self, graphics, *args, **kwargs):
        super(ContainerSprite, self).set_graphics(
            graphics, *args, **kwargs)

    def set_member_positions(self):
        style = self.style
        position_style = style["position_style"]
        border_size = style["border_size"]
        buffers = style["cell_buffer"]
        aligns = style["h_align"], style["v_align"]

        if position_style == "flow":
            self.table.set_member_positions_flow(
                self.position, self.size,
                border_size, buffers, aligns
            )

        elif position_style == "relative":
            for item in self.table.member_list:
                item.move(self.position)

        for item in self.table.member_list:
            if isinstance(item, ContainerSprite):
                item.set_member_positions()

    def set_group(self, group):
        super(ContainerSprite, self).set_group(group)

        self.add_members_to_group(group)

    def add_member_row(self, row):
        members = self.table.members
        members.append(row)
        self.set_members(members)

    def add_members_to_group(self, group):
        for sprite in self.table.member_list:
            if sprite not in group:
                sprite.set_group(group)

    def set_member_table(self, argument, *sections):
        if self.table.member_list:
            self.kill_members()

        if sections:
            file_name = argument
            members = []

            for section in sections:
                d = load_resource(file_name)[section]
                get_m = getattr(self, "get_members_from_" + section, False)

                if get_m:
                    plus = get_m(d, file_name)
                    members += plus
                else:
                    members += self.get_members_from_dict(d)

        else:
            if type(argument) is dict:
                members = self.get_members_from_dict(argument)

            elif type(argument) is list:
                members = self.get_members_from_list(argument)

            else:
                members = [[self.get_sprite_from_value(argument)]]

        self.set_members(members)

    def set_members(self, members):
        old = self.table.member_list
        self.table.members = members
        new = self.table.member_list

        for sprite in [s for s in old if s not in new]:
            sprite.kill()

        self.adjust_table()

        for group in self.groups:
            self.add_members_to_group(group)

        for item in self.table.member_list:
            item.add_listener(
                "on_change_size",
                {"name": "on_change_member_size",
                 "target": self}
            )

    def set_header(self, text):
        header = [self.get_header_row(text)]
        members = self.table.members

        self.set_members(header + members)

    def set_body(self, text):
        body = [[self.get_sprite_from_value(text)]]
        members = self.table.members

        self.set_members(body + members)

    def get_members_from_dict(self, d, header=False):
        get_box = self.get_text_box_from_value
        get_row = self.get_member_row_from_value

        if header:
            members = [self.get_header_row(header)]
        else:
            members = []

        for key in d:
            value = d[key]

            box = get_box(key)
            box.set_value(value)
            row = [box]
            row += get_row(value, key)

            members.append(row)

        return members

    def get_members_from_list(self, l, header=False):
        get_row = self.get_member_row_from_value

        if header:
            members = [self.get_header_row(header)]
        else:
            members = []

        i = 0

        for value in l:
            name = "index {}".format(i)
            members.append(get_row(value, name))
            i += 1

        return members

    def get_member_row_from_value(self, value, dict_name=None):
        get_sprite = self.get_sprite_from_value
        get_container = self.get_sprite_from_dict

        if not dict_name:
            name = "dict sprite"
        else:
            name = dict_name

        row = []

        if type(value) is dict:
            row.append(get_container(value, name))
            row[-1].style = {"border": False}

        else:
            row.append(get_sprite(value))

        return row

    def get_members_from_tables(self, d, file_name):
        members = [self.get_header_row(file_name)]

        for section in d:
            members += self.get_members_from_dict(
                d[section], header=section)

        return members

    def get_members_from_devices(self, d, file_name):
        name = file_name[:-4].replace("_", " ").capitalize()

        return self.get_members_from_dict(
            d, header=name)

    def get_members_from_info(self, d, file_name):
        header = file_name[:-4] + " info"
        members = self.get_members_from_dict(
            d, header=header)

        for row in members[1:]:
            i = 0

            for item in row:
                if i > 0:
                    for sub_row in item.table.members:
                        sub_row[1].style = "info_style"

                i += 1

        return members

    def get_header_row(self, text):
        header = self.get_sprite_from_value(text)
        header.style = "header_style"

        return [header]

    @staticmethod
    def get_sprite_from_value(value):
        sprite = Sprite(str(value))
        sprite.set_text(value)

        return sprite

    @staticmethod
    def get_text_box_from_value(value):
        name = str(value)
        sprite = ContainerSprite(name)
        sprite.set_member_table(value)

        return sprite

    @staticmethod
    def get_sprite_from_dict(d, name):
        sprite = ContainerSprite(name)
        sprite.set_member_table(d)

        return sprite

    def on_spawn(self):
        self.set_graphics(ContainerGraphics)

    def on_activate(self):
        for item in self.table.member_list:
            item.event_handler.queue_events(
                self.event
            )

    def on_select(self):
        for item in self.table.member_list:
            item.event_handler.queue_events(
                {"name": "on_select"}
            )

    def on_deselect(self):
        for item in self.table.member_list:
            item.event_handler.queue_events(
                {"name": "on_deselect"}
            )

    def on_death(self):
        super(ContainerSprite, self).on_death()

        for item in self.table.member_list:
            item.handle_event(self.event)

    def on_change_member_size(self):
        self.fix_size()


class OptionBlockSprite(ContainerSprite):
    def __init__(self, name):
        super(OptionBlockSprite, self).__init__(name)

        self.pointer = [0, 0]
        self.last = [-1, 0]

        self.activate_buttons = "A", "Start"
        self.dialog_table = DIALOG_TABLE.copy()

    def move_pointer(self, x, y):
        i, j = self.pointer
        start = [i, j]
        members = self.table.members

        cycling = True
        while cycling:
            if x != 0:
                j += x
                cells = len(members[i]) - 1

                if j > cells:
                    j = 0
                elif j < 0:
                    j = cells

            if y != 0:
                i += y
                rows = len(members) - 1

                if i > rows:
                    i = 0
                elif i < 0:
                    i = rows

            self.pointer = [i, j]
            try:
                cycling = not self.selected.selectable
            except IndexError:
                cycling = True

            if self.pointer == start:
                cycling = False

    @property
    def options(self):
        return [
            o for o in self.table.member_list if o.selectable
        ]

    @property
    def selected(self):
        return self.get_member(*self.pointer)

    @property
    def selected_index(self):
        return self.options.index(self.selected)

    def add_option_response(self, option, response):
        if type(response) is str:
            response = {"name": response}

        else:
            response = response.copy()

        if "target" not in response:
            response["target"] = self

        option.add_listener(
            "on_activate", response)

    def reset_menu(self):
        self.control_freeze = False
        self.last = [-1, 0]
        self.pointer = [0, 0]

        if self.table.member_list and not self.selected.selectable:
            for item in self.table.member_list:

                if item.selectable:
                    index = self.table.get_member_index(item)
                    self.pointer = index

                    self.select(index, sound=False)

                    break

    def on_death(self):
        super(OptionBlockSprite, self).on_death()

        if self.selected:
            self.selected.handle_event("on_deselect")

    def on_spawn(self):
        super(OptionBlockSprite, self).on_spawn()

        self.reset_menu()

        self.set_resources("menu_sounds")
        self.set_controller_interface("move_pointer", "activate", "return")

    def on_activate(self):
        option = self.selected
        option.handle_event(
            {"name": "on_activate"}
        )

        self.handle_menu_sound("activate")

    def on_return(self):
        self.handle_menu_sound("return")

    def show_block(self, block):
        for g in self.groups:
            block.set_group(g)

    def on_show_dialog(self):
        event = self.event
        name = event["dialog"]

        # if "dialog" name is in the zs.cfg "blocks" table, pull args
        if name in BLOCKS:
            d = BLOCKS[name].copy()

        else:
            d = {}

        # update dialog dict args with args from passed event
        d.update(event)

        # make dialog block sprite passing dialog_dict for args
        dialog = self.make_dialog_block(
            name, d)

        # add dialog response listener
        if "responses" in d:
            dialog.add_listener(
                "on_activate",
                {
                    "name": "on_dialog_response",
                    "target": self,
                    "sprite": dialog,
                    "responses": d["responses"]
                }
            )

        # add death listener
        if "on_death" in d:
            dialog.add_listener(
                "on_death", d["on_death"]
            )

        # switch control to dialog block
        self.handle_event({
            "name": "on_change_block",
            "block": dialog,
            "return_control": "on_death",
            "death": ("on_return", "on_activate")
        })

    def on_change_block(self):
        block = self.event["block"]

        if "group" not in self.event:
            self.show_block(block)
        else:
            block.set_group(
                self.event["group"])

        rc_event = self.event.get(
            "return_control", "on_return")
        death_events = self.event.get(
            "death", "on_return")

        # pass controller
        block.set_controller(
            self.controller.name
        )

        # cede / return control
        self.control_freeze = True

        block.add_listener(
            rc_event,
            {"name": "on_enable_control",
             "target": self}
        )

        # kill on death events
        if death_events:
            if type(death_events) is str:
                death_events = (death_events,)

            for name in death_events:
                block.add_listener(
                    name, "kill")

    def on_dialog_response(self):
        choice = self.event["sprite"].selected_index
        response = self.event.get("responses")

        try:
            response = response[choice]         # get response event name by option index
        except IndexError:                      # if select option doesn't have an
            response = False                    # indexed response event nothing happens
        except KeyError:
            response = False

        if response:                            # queue event if response found
            target = self
            if type(response) is dict and "target" in response:
                target = response["target"]

            target.queue_events(response)

    def handle_menu_sound(self, name):
        def listening(obj):
            en = "on_{}".format(name)
            return obj.event_handler.listening_for(en)

        if (
            listening(self) or listening(self.selected)
        ) and name in self.sounds:
            self.sounds[name].play()

    def select(self, pointer, sound=True):
        row, index = pointer
        lr, li = self.last

        last = self.get_member(lr, li)
        last.queue_events(
            {"name": "on_deselect"}
        )
        self.last = pointer

        option = self.get_member(row, index)
        option.queue_events(
            {"name": "on_select"}
        )

        if sound:
            select = self.sounds["select"]
            select.play()

    def update(self):
        super(OptionBlockSprite, self).update()

        if self.last != self.pointer:
            sound = True
            if self.last == [-1, 0]:
                sound = False

            row, index = self.pointer
            if self.get_member(row, index).selectable:
                self.select(self.pointer, sound=sound)

    def get_members_from_dict(self, d, header=False):
        members = super(OptionBlockSprite, self).get_members_from_dict(
            d, header=header)

        i = 0
        for row in members:
            if not (i == 0 and header):
                key = row[0]
                key.selectable = True

            i += 1

        return members

    def get_members_from_list(self, l, header=False):
        members = super(OptionBlockSprite, self).get_members_from_list(
            l, header=header)

        i = 0

        for row in members:
            if not (i == 0 and header):
                row[0].selectable = True

            i += 1

        return members

    def set_options(self, *args):
        for arg in args:
            if type(arg) is str:
                key_name = arg + "_option"
                if key_name in OPTIONS:
                    text = OPTIONS[key_name]["text"]
                    activate = EVENTS[
                        OPTIONS[key_name]["on_activate"]
                    ]

                else:
                    text = arg
                    activate = False

            else:
                text = arg["text"]
                event_name = arg["on_activate"]

                if event_name in EVENTS:
                    activate = EVENTS[event_name].copy()
                else:
                    activate = event_name

            option = self.get_sprite_from_value(text)
            option.selectable = True
            self.add_member_row([option])

            if activate:
                self.add_option_response(
                    option, activate)

    def set_dialog_table(self, table):
        if type(table) is str:
            self.dialog_table.update(
                TABLES[table]
            )

        else:
            self.dialog_table.update(table)

    def make_dialog_block(self, name, d):
        sprite = OptionBlockSprite(name)
        sprite.activate_buttons = self.activate_buttons

        # look up option text from dialog table

        key = "_".join(name.split("_")[:-1])                # dialog table lookup key "..._..._dialog"
        table = self.dialog_table
        options = sorted([                                  # add dialog options from table entries
            k for k in table if key == "_".join(
                k.split("_")[:-1])                          # indexed by number
        ])

        # substitute strings using format method and passed "format" dict

        f_dict = d.get("format", {})                        # format dialog for {key_names}
        options = [
            table[o].format(**f_dict) for o in options
        ]                                                   # substitute dialog text per indexes

        # passed "body" argument takes precedence over dialog table header

        if "body" not in d:
            d["body"] = table[key].format(**f_dict)         # use table key to get body text

        # passed "options" argument is added first, followed by dialog table args

        if "options" in d:
            d["options"] = options + d["options"]           # merge table options with
        else:
            d["options"] = options                          # options passed in d

        # assign default dialog position if not set

        if "position" not in d:
            d["position"] = list(DIALOG_POSITION)

        init_item({}, table, sprite, d, warning=False)      # initialize the sprite

        return sprite


class HudBoxSprite(ContainerSprite):
    def __init__(self, name):
        super(HudBoxSprite, self).__init__(name)

        self.fields = []
        self.model_manager = ModelManager(self)
        self.target = None

        self.INIT_ORDER = ContainerSprite.INIT_ORDER + [
            "target", "fields"
        ]

    def set_target(self, target):
        self.target = target

    def add_field(self, d):
        if type(d) is str:
            d = load_resource("hud_fields")[d]

        value_name = d["value_name"]
        obj = self.target
        reporter = HudFieldSprite(value_name)

        get_text = d.get("get_text", False)
        if type(get_text) is str:
            get_text = getattr(self, get_text)

        reporter.set_text_function(get_text)

        cache_args = d.get("cache")
        size = d.get("cache_size", 1)

        if cache_args:
            args = cache_args
        else:
            args = ["cache"]

        reporter.set_cache_style(size, *args)

        get_value = d.get("get_value", None)

        self.model_manager.link_value(
            value_name, obj, get_value
        )
        self.model_manager.link_object(
            value_name, reporter, "set_cache"
        )

        self.add_member_row([
            self.get_sprite_from_value(value_name + ":"),
            reporter
        ])

    def set_fields(self, *fields):
        for field in fields:
            self.add_field(field)

    def update(self):
        super(HudBoxSprite, self).update()
        self.model_manager.update()

    def on_spawn(self):
        super(HudBoxSprite, self).on_spawn()

        self.set_style("seethru_bg_style")

    @staticmethod
    def format_float(*numbers):
        f_str = "{:4." + str(PRECISION) + "f}"

        def format_number(num):
            num = round(num, PRECISION + 1)

            if int(num) == num:
                return str(int(num))

            else:
                return f_str.format(num)

        if len(numbers) == 1:
            return format_number(numbers[0])

        else:
            return "({})".format(
                ", ".join(
                    [format_number(n) for n in numbers])
            )

    @staticmethod
    def format_point(point):
        return HudBoxSprite.format_float(*point)

    @staticmethod
    def format_vector(vector):
        return HudBoxSprite.format_point(vector.get_value())


class HudFieldSprite(Sprite):
    def __init__(self, name):
        super(HudFieldSprite, self).__init__(name)

        self.cache = None
        self.cache_args = ["cache"]
        self.text_function = None
        self.update_timer = Timer(
            name + " update timer", HUD_FREQUENCY,
            on_switch_off=self.update_field, temp=False)

    def set_cache_style(self, size, *args):
        cls = "cache"
        if args:
            cls = args[0]
            self.cache_args = args

        cls_dict = {
            "cache": CacheList,
            "average": AverageCache,
            "change": ChangeCache
        }

        self.cache = cls_dict[cls](size)

    def set_text_function(self, function):
        self.text_function = function

    def set_cache(self, item):
        self.cache.append(item)

    def get_cache_text(self):
        cache = self.cache
        args = self.cache_args
        cls = args[0]
        text = ""

        if self.text_function:
            text_func = self.text_function

        else:
            text_func = str

        if cls == "cache":
            text = "\n".join([text_func(item) for item in cache])

        if cls == "average":
            text = text_func(cache.average())

        if cls == "change":
            maximum = args[1]
            text = "\n".join(
                [text_func(item) for item in cache.changes(maximum)]
            )

        return text

    def update(self):
        super(HudFieldSprite, self).update()

        timer = self.update_timer
        timer.tick()

        if timer.is_empty():
            timer.reset()

    def update_field(self):
        change = self.get_text() != self.get_cache_text()

        if change:
            self.set_text(self.get_cache_text())


class VectorSprite(Sprite):
    def __init__(self, name):
        super(VectorSprite, self).__init__(name)

        self.vector = Vector(name, 0, 0)
        self.vector_origin = 0, 0
        self.draw_width = 5
        self.draw_color = 255, 255, 255

    def set_name(self, name):
        super(VectorSprite, self).set_name(name)

        self.vector.name = name

    def move(self, dxdy):
        super(VectorSprite, self).move(dxdy)

        x, y = dxdy
        ox, oy = self.vector_origin
        ox += x
        oy += y
        self.vector_origin = ox, oy

    @property
    def draw_point(self):
        return self.vector.get_draw_point(
            self.vector_origin, self.draw_width)

    def on_spawn(self):
        self.graphics = VectorGraphics(self)
        self.vector_origin = self.position
        self.reset_vector()

    def set_draw_width(self, width):
        self.draw_width = width

    def set_draw_color(self, color):
        self.draw_color = color

    def set_value(self, value):
        i, j = value
        self.vector.set_value(i, j)

    def reset_vector(self):
        self.graphics.reset_image()

        self.rect.position = self.draw_point

    def get_collision(self, sprite):
        sprite = self.model[sprite]
        w = Wall.get_from_vector(sprite.vector, sprite.position)

        y_int = self.vector.get_y_intercept(self.position)

        if y_int:
            y_int = round(y_int)

        ac = w.axis_collision(self.vector, self.position)
        if ac:
            ax, ay = ac
            ax = round(ax)
            ay = round(ay)
            ac = ax, ay
        vc = w.vector_collision(self.vector, self.position)
        if vc:
            vx, vy = vc
            vx = round(vx)
            vy = round(vy)
            vc = vx, vy

        angle = str(self.vector.get_angle())
        y_int = "Y_intercept:\t {}\n".format(y_int)
        ac = "axis_collision:\t {}\n".format(ac)
        vx = "vector_collision:\t {}".format(vc)

        return angle + "\n" + y_int + ac + vx
