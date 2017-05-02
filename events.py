from classes import Timer


class EventHandler:
    def __init__(self, entity):
        self.entity = entity
        self.paused = []
        self.listeners = []

    def __repr__(self):
        e = repr(self.entity)

        return "EventHandler for {}".format(e)

    def set_action(self, action):
        action = self.interpret(action)
        name = action["name"]
        duration = action.get("duration", 1)
        lerp = action.get("lerp", True)
        link = action.get("link", False)

        def do_action():
            self.entity.handle_event(action)

        timer = Timer(name, duration)

        if lerp:
            timer.on_tick = do_action

        else:
            timer.on_switch_off = do_action

        if link:
            timer.on_switch_off = lambda: self.set_action(link)

        action["timer"] = timer
        self.entity.clock.add_timers(
            timer)

    def queue_events(self, *events):
        if len(events) > 1:
            i = 0

            for e in events[1:]:
                events[i]["link"] = e
                i += 1

        self.set_action(events[0])

    def handle_event(self, event):
        event = self.interpret(event)
        name = event["name"]

        if name not in self.paused:
            m = getattr(self.entity, name, False)
            if m and callable(m):
                self.entity.set_event(event)
                m()

        for listener in self.listeners:
            hear = listener["name"] == event["name"]

            if hear:
                target = listener["target"]
                response = listener.get("response", event)
                target.queue_events(response)

                if listener.get("temp", False):
                    self.remove_listener(listener)

    def remove_listener(self, listener):
        i = 0

        for l in self.listeners:
            if l is listener:
                self.listeners.pop(i)
            i += 1

    def listening_for(self, event_name):
        for l in self.listeners:
            if l["name"] == event_name:
                return True

        return False

    @staticmethod
    def interpret(argument):
        if type(argument) is dict:
            return argument

        if type(argument) is str:
            return {"name": argument}
