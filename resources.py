from zs_constants import CFG, JSON, IMAGES, IMAGE_EXT, SOUNDS, SOUND_EXT, STYLES
from zs_cfg import load_cfg, load_json

from os.path import join
from os import listdir

# PYGAME CHOKE POINT

import pygame


def get_path(directory, file_name):
    names = [f for f in listdir(directory) if f[0] not in "._"]
    files = [n for n in names if "." in n]
    dirs = [n for n in names if n not in files]

    if file_name in files:
        return join(directory, file_name)

    else:
        found = False

        for d in dirs:
            try:
                return get_path(
                    join(directory, d), file_name)

            except FileNotFoundError:
                pass

    if not found:
        raise FileNotFoundError(join(directory, file_name))


def load_resource(file_name):
    if "." not in file_name:
        return load_resource("zs.cfg")[file_name]

    else:
        ext = file_name.split(".")[-1]

        if ext == CFG:
            path = get_path(CFG, file_name)

        elif ext == JSON:
            path = join(JSON, file_name)

        elif ext in IMAGE_EXT:
            path = join(IMAGES, file_name)

        elif ext in SOUND_EXT:
            path = join(SOUNDS, file_name)

        else:
            raise IOError(
                "bad file extension for {}".format(file_name)
            )

    return get_object(ext, path)


def get_object(ext, path):
    if ext == CFG:
        return load_cfg(path)

    if ext == JSON:
        return load_json(path)

    if ext in IMAGE_EXT:
        # PYGAME CHOKE POINT

        return pygame.image.load(path)

    if ext in SOUND_EXT:
        # PYGAME CHOKE POINT

        return pygame.mixer.Sound(path)


def get_font(name, size, bold, italic):
    # PYGAME CHOKE POINT

    path = pygame.font.match_font(name, bold, italic)
    font = pygame.font.Font(path, size)

    return font


DEFAULT_STYLES = load_resource(STYLES)
DEFAULT_STYLE = DEFAULT_STYLES["default_style"]


def load_style(style_name):
    sd = DEFAULT_STYLE.copy()
    sd.update(
        DEFAULT_STYLES[style_name])

    return sd
