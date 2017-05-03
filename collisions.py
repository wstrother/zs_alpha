from entities import Layer
from physics import PhysicsInterface
from sprites.animation_sprite import HitboxManager


class CollisionManager:
    def __init__(self, name):
        self.name = name

        self.collision_system = None
        self.group_a = []
        self.group_b = []

    def __repr__(self):
        return "CollisionManager: {}".format(self.name)

    def update(self):
        if self.collision_system:
            if self.group_b:
                self.collision_system(
                    self.group_a, self.group_b)

            else:
                self.collision_system(
                    self.group_a)

    def set_group_a(self, group):
        self.group_a = group

    def set_group_b(self, group):
        self.group_b = group

    @staticmethod
    def sprite_region_collision_system(sprites, regions):
        for sprite in sprites:
            for region in regions:
                collision = region.test_sprite_collision(sprite)

                if collision:
                    region.handle_sprite_collision(sprite, collision)

    @staticmethod
    def group_perm_collision_system(group, test, handle):
        tested = []
        for item in group:
            tested.append(item)

            for other in [o for o in group if o not in tested]:
                collision = test(item, other)

                if collision and handle:
                    handle(item, other, collision)

    @staticmethod
    def sprite_sprite_collision_system(group):
        test = PhysicsInterface.test_sprite_collision
        handle = PhysicsInterface.handle_sprite_collision

        CollisionManager.group_perm_collision_system(
            group, test, handle)

    @staticmethod
    def sprite_hitbox_collision_system(group):
        test = HitboxManager.do_hitbox_collision

        CollisionManager.group_perm_collision_system(
            group, test, None)

    @staticmethod
    def get_from_dict(d):
        cm = CollisionManager(d["name"])

        cm.group_a = d["group_a"]
        cm.group_b = d.get("group_b", [])

        system_name = d["collision_system"] + "_collision_system"
        cm.collision_system = getattr(CollisionManager, system_name)

        return cm


class CollisionLayer(Layer):
    def __init__(self, name):
        super(CollisionLayer, self).__init__(name)

        self.collision_systems = []

    def set_collisions(self, *systems):
        for s in systems:
            s = s.copy()
            s["group_a"] = self.model[s["group_a"]]

            b = s.get("group_b")
            if b:
                s["group_b"] = self.model[s["group_b"]]

            self.collision_systems.append(
                CollisionManager.get_from_dict(s)
            )

    def get_update_methods(self):
        um = super(CollisionLayer, self).get_update_methods()

        um += [
            self.update_collision_systems
        ]

        return um

    def update_collision_systems(self):
        for system in self.collision_systems:
            system.update()
