import json

from os.path import join

from collections import OrderedDict

from zs_constants import CFG, JSON, START_ENV

ORDERED_SECTIONS = ["populate", "state_transitions", "layers"]


# loads a text string from a cfg formatted file
def load_cfg(file_name):
    file = open(file_name, "r")
    text = file.read()
    file.close()

    return get_cfg(text)


def save_cfg(d, file_name):
    file = open(file_name, "w")

    text = ""

    for section in d:
        text += "# " + section + "\n\n"

        text += format_dict(d[section])

    print(text)
    file.write(text)
    file.close()


# loads a dict from a json formatted file
def load_json(file_name):
    file = open(file_name, "r")
    d = json.load(file)
    file.close()

    return d


# saves a dict to a json formatted file
def save_json(d, file_name):
    file = open(file_name, "w")
    json.dump(d, file)
    file.close()


# checks if string from file can be converted to int or float
# returns value as int or float if possible and string if not
def string_to_number(s):
    try:
        num = float(s)
        if num.is_integer():
            num = int(num)

        return num
    except ValueError:
        return s


# prints dict items with recursive indentation
def print_dict(d, t=0):
    print(format_dict(d, t=t))


def format_dict(d, t=0):
    output = ""

    tab = "\t" * t

    for key in d:
        value = d[key]
        if type(value) is dict:

            output += tab + key + "\n"

            output += format_dict(value, t=t + 1) + "\n"

        else:
            if type(value) is list:
                rhs = ", ".join([str(item) for item in value])
            else:
                rhs = str(value)

            output += tab + str(key) + ": " + rhs + "\n"

    return output


# get a dict object from a cfg formatted string of text
def get_cfg(text):
    sections = text.split("#")
    cfg = {}

    for section in [s for s in sections if s]:
        name = section.split("\n")[0][1:]

        if name not in ORDERED_SECTIONS:
            cfg[name] = get_section(section)
        else:
            cfg[name] = get_section(section, ordered=True)

    return cfg


# get a dict object from a single section of cfg formatted text
def get_section(text, ordered=False):
    items = text.split("\n\n")
    names = []

    if not ordered:
        section = {}
    else:
        section = OrderedDict()

    for item in [i for i in items if i]:
        if item[0] != " ":
            name = item.split("\n")[0]

            if name not in names:
                section[name] = get_item(item)
                names.append(name)

            else:
                if type(section[name]) is dict:
                    s1 = section[name]
                    section[name] = [s1]

                section[name].append(get_item(item))

    return section


# get a dict object from a single cfg formatted item expression
def get_item(text):
    lines = text.split("\n")
    item = {}

    for line in [l for l in lines if l]:
        if line[0] == "\t":
            line = line[1:]
            if ":" not in line:
                key = string_to_number(line)
                item[key] = True

            else:
                key, value = line.split(": ")
                key = string_to_number(key)

                if value[0] == "\"" and value[-1] == "\"":
                    value = value[1:-1]

                elif "," not in value:
                    value = string_to_number(value)

                elif value[-1] == ",":
                    value = [string_to_number(value[:-1]), ]

                elif "(" not in value:
                    args = value.split(", ")
                    if args[-1] == "":
                        args = args[:-1]

                    value = [string_to_number(v) for v in args]

                else:
                    args = value[1:-1].split(", ")
                    if args[-1] == "":
                        args = args[:-1]

                    value = tuple([string_to_number(v) for v in args])

                item[key] = value

    return item

if __name__ == "__main__":
    title = START_ENV

    path = join(CFG, title + ".cfg")
    cfg = load_cfg(path)

    path = join(JSON, title + ".json")
    save_json(cfg, path)

    format_dict(cfg)
