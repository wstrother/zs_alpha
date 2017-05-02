from resources import load_resource


class CacheList(list):
    def __init__(self, size):
        super(CacheList, self).__init__()
        self._size = size

    def set_size(self):
        if len(self) > self._size:
            for i in range(len(self) - 1):
                self[i] = self[i + 1]
            self.pop()

    def append(self, p_object):
        super(CacheList, self).append(p_object)
        self.set_size()

    def __iadd__(self, other):
        for item in other:
            self.append(item)

        return self


class AverageCache(CacheList):
    def average(self):
        if not self:
            return []

        if type(self[0]) in (int, float):
            return sum(self) / len(self)

        else:
            lhs = [i[0] for i in self]
            rhs = [i[1] for i in self]

            return (sum(lhs) / len(lhs)), (sum(rhs) / len(rhs))


class ChangeCache(CacheList):
    def changes(self, maximum):
        changes = []
        last = None
        for item in self:
            if item != last:
                last = item
                changes.append(item)

        if len(self) > maximum:
            return changes[-maximum:]

        else:
            return changes


class Group:
    def __init__(self, name):
        self.name = name
        self._items = []

    def __iter__(self):
        return iter(self._items)

    def __repr__(self):
        return "Group: {} {}".format(self.name, self._items)

    def add_item(self, *items):
        for item in items:
            self._items.append(item)
            item.groups.append(self)

    def remove_item(self, item):
        item.groups = [g for g in item.groups if g is not self]
        self._items = [s for s in self._items if s is not item]


class MemberTable:
    """
    A MemberTable object contains a list of 'row' lists that represent
    a table of items. It provides methods for adding and replacing
    items in the table as well as entire rows. It also includes a
    property 'member_list' that returns a list of each item in the
    table, iterating through each item in each row one at a time.
    """
    def __init__(self, name, members=None):
        self.name = name

        if not members:
            members = []
        self.members = members

    # the add_member() method serves as a subclass hook that will define
    # the 'default' adding behavior. By default, it takes a single
    # tuple: (row index, item index) as the only argument and passes it
    # to 'set_member_at_index'
    def add_member(self, item, index=None):
        if not index:
            index = self.get_new_index()
        self.set_member_at_index(item, index)

    def get_new_index(self):
        row = len(self.members) - 1
        cell = len(self.members[row])

        return row, cell

    def set_member_at_index(self, item, index):
        row_index, cell_index = index
        m = self.members

        max_i = len(m) - 1
        if row_index > max_i:
            add_rows = row_index - max_i

            for row in range(add_rows):
                m.append([])

        row = m[row_index]
        max_j = len(row) - 1
        if cell_index > max_j:
            add_cols = cell_index - max_j
            for cell in range(add_cols):
                    row.append(None)

        self.members[row_index][cell_index] = item

    def add_row(self, row):
        if not self.members[0]:
            self.members[0] = row
        else:
            self.members.append(row)

    def remove_member(self, index):
        row_index, cell_index = index
        row = self.members[row_index]
        member = row.pop(cell_index)

        if not row:
            self.members.pop(row_index)

        return member

    def remove_row(self, index):
        return self.members.pop(index)

    def get_member_index(self, member):
        r = 0
        i = 0
        for row in self.members:
            for item in row:
                if item is member:
                    return [r, i]

                i += 1

            r += 1
            i = 0

        return [r, i]

    @property
    def member_list(self):
        m = []
        for row in self.members:
            for item in row:
                m.append(item)

        return m

    def print_members(self):
        print(self.str_members())

    def str_members(self, sep="|"):
        m = ""
        for row in self.members:
            r = []
            for item in row:
                r.append(str(item))

            line = (sep + " " + sep).join(r)
            m += (sep + "{}" + sep + "\n").format(line)

        return m


class Meter:
    """
    Meter objects have a minimum, value, and maximum attribute (int or float)
    The normalize method is called when one of these attributes is assigned to
    ensuring that value stays in the proper range.

    Use of property objects as attributes allows for some automatic edge case
    handling. Be aware that by design Meter objects will try to make assignments
    work rather than throw errors. E.G. passing a minimum lower than maximum
    to __init__ raises ValueError, but the 'maximum' / 'minimum' setters will
    automatically normalize assignments to an acceptable range.

    Meter is designed to make composed attributes and to allow for flexible
    dynamic use so if you want to ensure edge case errors, that logic will
    need to be implemented by the relevant Entity in the game engine.
    """
    # Meter(name, value) ->                     minimum = 0, value = value, maximum = value
    # Meter(name, value, maximum) ->            minimum = 0, value = value, maximum = maximum
    # Meter(name, minimum, value, maximum) ->   minimum = 0, value = value, maximum = maximum
    def __init__(self, name, *args):
        value = args[0]
        maximum = args[0]
        minimum = 0
        if len(args) == 2:
            maximum = args[1]
        if len(args) == 3:
            minimum = args[0]
            value = args[1]
            maximum = args[2]

        self.name = name
        self._value = value
        self._maximum = maximum
        self._minimum = minimum

        if maximum < minimum:     # minimum should always be leq than maximum
            raise ValueError("bad maximum / minimum values passed to meter object")
        self.normalize()

    def __repr__(self):
        sf = 4
        n, v, m, r = (self.name,
                      round(self.value, sf),
                      round(self._maximum, sf),
                      round(self.get_ratio(), sf))

        return "{}: {}/{} r: {}".format(n, v, m, r)

    # getters and setters
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.normalize()

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        if value > self.maximum:
            value = self.maximum

        self._minimum = value
        self.normalize()

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        if value < self.minimum:
            value = self.minimum

        self._maximum = value
        self.normalize()

    # methods
    def normalize(self):        # sets value to be inside min / max range
        in_bounds = True

        if self._value > self.maximum:
            self._value = self.maximum
            in_bounds = False

        if self._value < self.minimum:
            self._value = self.minimum
            in_bounds = False

        # this return value is mainly for debugging
        # and unit testing
        return in_bounds

    def refill(self):
        self.value = self.maximum

        return self.value

    def reset(self):
        self.value = self.minimum

        return self.value

    def get_ratio(self):
        span = self.get_span()
        value_span = self.value - self.minimum

        if span != 0:
            return value_span / span
        else:
            # calling "get_ratio" on a Meter object with a span of 0
            # will raise an ArithmeticError. There's no real way to
            # handle this edge case dynamically without creating
            # very weird, unintuitive behavior
            raise ArithmeticError("meter object has span of 0")

    def get_span(self):
        return self.maximum - self.minimum

    def is_full(self):
        return self.value == self.maximum

    def is_empty(self):
        return self.value == self.minimum

    def next(self):
        if self.is_full():
            self.reset()
        else:
            self.value += 1
            if self.value > self.maximum:
                dv = self.value - self.maximum
                self.value = dv

        return self.value

    def prev(self):
        if self.is_empty():
            self.refill()
        else:
            self.value -= 1
            if self.value < self.minimum:
                dv = self.value - self.minimum
                self.value = self.maximum - dv

        return self.value

    def shift(self, val):
        dv = abs(val) % (self.get_span() + 1)
        if val > 0:
            for x in range(dv):
                self.next()
        if val < 0:
            for x in range(dv):
                self.prev()

        return self.value


class Timer(Meter):
    """
    Timer objects have a set duration stored as frames.

    An optional on_tick() method is called on every frame the timer is
    ticked, and the on_switch_off() method is called on the frame that the
    Timer's value reaches 0.

    The temp flag determines if the timer will be removed by the Clock
    object that calls it's tick() method.
    """
    def __init__(self, name, duration, temp=True,
                 on_tick=None, on_switch_off=None):
        if duration <= 0:
            raise ValueError("bad duration", 0)
        super(Timer, self).__init__(name, duration)

        self.is_off = self.is_empty
        self.reset = self.refill
        self.temp = temp

        if on_tick:
            self.on_tick = on_tick
        if on_switch_off:
            self.on_switch_off = on_switch_off

    def __repr__(self):
        sf = 4
        n, v, m = (self.name,
                   round(self.value, sf),
                   round(self._maximum, sf))

        return "Timer: {} {}/{}".format(n, v, m)

    def is_on(self):
        return not self.is_off()

    def get_ratio(self):
        r = super(Timer, self).get_ratio()

        return 1 - r    # r should increment from 0 to 1 as the timer ticks

    def tick(self):
        before = self.is_on()

        self.value -= 1
        self.on_tick()

        after = self.is_off()
        switch_off = before and after

        if switch_off:
            self.on_switch_off()

        return switch_off

    def on_tick(self):
        pass

    def on_switch_off(self):
        pass


class ChargeMeter(Meter):
    def __init__(self, name, maximum, check_func, clear_func=None):
        super(ChargeMeter, self).__init__(name, maximum)
        self.check = check_func
        self.clear_func = clear_func

    def update(self):
        if self.check():
            self.value += 1

        else:
            if self.value and self.clear_func:
                self.clear_func(self)
            self.reset()


class LerpMeter(Meter):
    def __init__(self, name, func):
        super(LerpMeter, self).__init__(name, 0, 1)
        self.func = func

    def get_func_value(self):
        return self.func(self.value)


class Clock:
    """
    A Clock object simply contains a list of timers and calls
    tick() on each once per frame (assuming it's tick() method
    is called once per frame).

    A 'queue' and 'to_remove' list are used to create a one frame
    buffer between add_timers() and remove_timer() calls. This helps
    avoid some bugs that would break the for loop in tick() if another
    part of the stack calls those methods before the tick() method has
    fully executed.

    Timers with the temp flag set are removed when their value reaches 0
    but are reset on the frame their value reaches 0 if the flag is not
    set.
    """
    def __init__(self, name, timers=None):
        self.name = name
        self.timers = []
        self.queue = []
        self.to_remove = []

        if timers:
            self.add_timers(*timers)

    def __repr__(self):
        return self.name

    def add_timers(self, *timers):
        for timer in timers:
            self.queue.append(timer)

    def remove_timer(self, name):
        to_remove = []

        for t in self.timers:
            if t not in self.to_remove:     # remove_timer() checks the queue list
                if t.name == name:          # for matches as well as the active
                    to_remove.append(t)     # timers list

        for t in self.queue:
            if t not in self.to_remove:
                if t.name == name:
                    to_remove.append(t)

        self.to_remove += to_remove

    def tick(self):
        for t in self.queue:                # add queue timers to active timers list
            if t not in self.to_remove:     # unless that timer is set to be removed
                self.timers.append(t)

        self.queue = []
        tr = self.to_remove
        timers = [t for t in self.timers if t not in tr]

        for t in timers:
            t.tick()

            if t.is_off():              # timers without the temp flag set to True
                if not t.temp:          # will be reset when their value reaches 0
                    t.reset()
                else:
                    self.to_remove.append(t)

        self.timers = [t for t in timers if t not in tr]
        self.to_remove = []


class StateMachine:
    def __init__(self, name):
        self.name = name
        self.transitions = {}

        self._state = None
        self.states = None
        self.buffer_state = False

    def set_transitions(self, obj, file_name):
        cfg = load_resource(file_name)

        states = list(cfg["state_transitions"].keys())
        self.set_states(*states)

        for state in states:
            entry = cfg["state_transitions"][state]

            for transition in list(entry.keys()):
                args = entry[transition]
                to_state = args[0]
                t = {}

                method_name = transition
                if transition[0:4] == "not_":
                    method_name = transition[4:]
                    t["logic"] = False

                t["name"] = transition
                t["to_index"] = self.get_state_index(to_state)
                t["buffer"] = "buffer" in args

                if not method_name == "auto":
                    t["check"] = getattr(obj.controller_interface, method_name)

                else:
                    t["check"] = "auto"

                entry[transition] = t

        self.transitions = cfg["state_transitions"]

    def set_states(self, *states):
        self.states = list(states)
        self._state = Meter(
            "state machine meter",
            0, 0, len(states))

    def set_state(self, state):
        if type(state) is str:
            value = self.get_state_index(state)

        elif type(state) is int:
            value = state

        else:
            raise TypeError("{} not int or str".format(state))

        self._state.value = value
        self.buffer_state = False

    def get_state(self):
        i = self._state.value

        return self.states[i]

    def check_transition(self, transition):
        if not transition["check"] == "auto":
            check = bool(transition["check"]())
        else:
            check = self.auto()

        logic = transition.get("logic", True)

        return check == logic

    def get_state_index(self, state):
        return self.states.index(state)

    def update(self):
        transitions = self.transitions[
            self.get_state()
        ]

        if self.buffer_state is not False:
            t = {"check": self.auto}

            if self.check_transition(t):
                self.set_state(self.buffer_state)
                return

        for t in transitions.values():
            to_index = t["to_index"]
            check = self.check_transition(t)
            buffer = t.get("buffer", False)

            if check:
                if not buffer:
                    self.set_state(to_index)

                else:
                    self.buffer_state = to_index

    def auto(self):
        return True


LOG_SIZE = 20


class MessageLogger:
    def __init__(self):
        self._log = CacheList(LOG_SIZE)
        self.name = None

    def log(self, message, *args):
        if args:
            message = (message,) + args

        self._log.append(str(message))

    def get_message(self):
        if self._log:
            return self._log[-1]

        else:
            return ""

    def get_log(self, depth):
        if self._log:
            return "\n".join(self._log[-depth:])

        else:
            return []
