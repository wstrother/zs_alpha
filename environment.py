from sys import exit

from classes import Group
from context_manager import update_model, add_layers, populate
from entities import Layer, Sprite, ModelManager, Region
from graphics import ContainerGraphics, TextGraphics, RectGraphics
from layers.utils import DrawRectLayer, PauseMenuLayer, DrawVectorLayer
from resources import load_resource
from sprites.animation_sprite import AnimationSprite
from sprites.gui import OptionBlockSprite, ContainerSprite, HudBoxSprite, VectorSprite
from sprites.menus import ControllerMenu, EnvironmentMenu, PauseMenu
from geometry import Vector, Wall
from collisions import CollisionLayer


class Environment(Layer):
    CLASS_DICT = {
        "layer": Layer,
        "sprite": Sprite,
        "vector": Vector,
        "region": Region,
        "wall": Wall,
        "model_manager": ModelManager,
        # GRAPHICS
        "container_graphics": ContainerGraphics,
        "text_graphics": TextGraphics,
        "rect_graphics": RectGraphics,
        # LAYERS
        "draw_rect_layer": DrawRectLayer,
        "pause_menu_layer": PauseMenuLayer,
        "draw_vector_layer": DrawVectorLayer,
        "collision_layer": CollisionLayer,
        # SPRITES
        "pause_menu": PauseMenu,
        "controller_menu": ControllerMenu,
        "environment_menu": EnvironmentMenu,
        "option_block_sprite": OptionBlockSprite,
        "container_sprite": ContainerSprite,
        "animation_sprite": AnimationSprite,
        "hud_box_sprite": HudBoxSprite,
        "vector_sprite": VectorSprite
    }

    def __init__(self, name, *controllers):
        super(Environment, self).__init__(name)

        self.model["environment"] = self
        self.cfg = load_resource(name)

        for c in controllers:
            try:
                self.set_controller(c, clear=False)
            except IOError:
                print("\n\nfailed to load controller {}".format(c))

        update_model(
            self.CLASS_DICT, self.cfg,
            self.model)

        if "layers" in self.cfg:
            add_layers(
                self.CLASS_DICT, self.cfg,
                self)

        self.transition = False
        self.return_env = None

    def get_groups(self):
        groups = []

        for name in self.model:
            item = self.model[name]

            if isinstance(item, Group):
                groups.append(item)

        return groups

    def get_layers(self):
        layers = []

        for name in self.model:
            item = self.model[name]

            if isinstance(item, Layer):
                layers.append(item)

        return layers

    def on_spawn(self):
        populate(
            self.CLASS_DICT,
            self.cfg,
            self.model)

        for g in self.get_groups():
            for item in g:
                item.set_event_passers(
                    self, "on_exit"
                )

        for layer in self.sub_layers:
            layer.set_event_passers(
                self, "on_exit"
            )

    def on_exit(self):
        e = self.event
        env = e.get("environment", False)

        self.kill()
        self.add_listener("on_death", {
            "name": "on_change_environment",
            "environment": env
        })

    def on_change_environment(self):
        e = self.event
        env = e.get("environment", False)

        if env:
            self.transition = env

        else:
            return_env = self.return_env

            if return_env:
                e["to_parent"] = True
                self.transition = return_env

            else:
                exit()

        # self.return_env = None
