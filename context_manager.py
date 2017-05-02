from classes import Group

ADD_TO_MODEL = "add_to_model"


def get_spawn_method(class_dict, cls):
    def spawn(n):
        return class_dict[cls](n)

    return spawn


def update_model(class_dict, cfg, model):
    for section in cfg:
        for name in cfg[section]:
            entry = cfg[section][name]

            # groups

            if section == "groups":
                item = Group(name)

            # layers

            elif section == "layers":
                item = get_spawn_method(
                    class_dict, entry["class"])(name)

            # items

            # elif section == "items":
            #     item = get_spawn_method(
            #         class_dict, entry["class"])

            else:
                item = entry

            if section != "populate":
                model[name] = item


def add_layers(class_dict, cfg, environment):
    layers = cfg["layers"]
    model = environment.model

    for name in layers:
        #                       # Add / initialize layer objects for environment
        d = layers[name]
        layer = model[name]

        if "parent_layer" not in d:
            environment.sub_layers.append(layer)

        init_item(
            class_dict, model, layer, d
        )


def populate(class_dict, cfg, model):
    pd = cfg["populate"]
    items = cfg.get("items", {})

    for name in pd:           # add item instances to groups
        entry = pd[name]
        entries = []

        if type(entry) is dict:
            entries = [entry]

        elif type(entry) is list:
            entries = entry

        for e in [e for e in entries if e]:
            #                       # Add / initialize sprite objects for environment

            d = e.copy()
            if name in items:
                d.update(items[name])

            spawn = get_spawn_method(
                class_dict, d["class"])

            item = spawn(name)

            init_item(
                class_dict, model,
                item, d
            )

            if ADD_TO_MODEL in e:
                model[item.name] = item


INIT_KEYS = (ADD_TO_MODEL,)


def init_item(class_dict, model, item, item_dict, warning=True):
    # print("\nINITIALIZING ", item)
    # allow item to define a required order for init method calls

    keys = [k for k in item_dict if k != "class"]
    order = list(getattr(item, "INIT_ORDER", []))

    if order:
        attrs = [o for o in order if o in keys] + [k for k in keys if k not in order]
    else:
        attrs = keys

    # call set_attribute methods on item for values in dict

    for attr in attrs:
        set_attr = "set_" + attr
        # print("\t", set_attr)

        if hasattr(item, set_attr):

            # match value keys from CONTEXT_DICT and model

            value = get_value_from_keys(
                item_dict[attr], class_dict, model)

            if type(value) is list:
                args = value
            else:
                args = [value]

            # print("\targs:", args, "\n")
            getattr(item, set_attr)(*args)

        elif attr not in INIT_KEYS:
            msg = "no {} method for {}".format(
                set_attr, item)

            if warning:
                # raise ValueError(msg)
                print("\n\t!!!!!!!!\n\t", msg)


def get_value_from_keys(value, class_dict, model):

    def get(k, cd, m):
        escape = False
        if type(k) is str and k[0] == "$":
            escape = True

        if not escape:
            if k == "model":
                return m

            if k in cd:
                return cd[k]

            if k in m:
                return m[k]

            else:
                return k

        if escape:
            return k[1:]

    if type(value) is list:
        new = []
        for item in value:
            new.append(
                get(item, class_dict, model)
            )

        return new

    elif type(value) is dict:
        for key in value:
            if value[key] is True:
                value[key] = get(key, class_dict, model)

    else:
        return get(value, class_dict, model)
