from sys import exit

import pygame

from environment import Environment
from zs_constants import SCREEN_SIZE, FRAME_RATE, START_ENV, START_CONTROLLERS

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(buffer=256)


class Game:
    """
    The Game object is used to sync a game environment / data model with a display surface
    and update them both at a regular interval.
    """

    def __init__(self, screen, frame_rate, start_env):
        self.environment = start_env
        self.screen = screen
        self.frame_rate = frame_rate

    '''This method is necessary to poll and clear the Pygame events queue, as well as
    checking for QUIT events to close the program'''
    @staticmethod
    def poll_events():
        # PYGAME CHOKE POINT

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

    def main(self):
        # PYGAME CHOKE POINT

        clock = pygame.time.Clock()         # clock object used to set max frame_rate

        while True:
            self.poll_events()
            self.main_routine(clock)
            pygame.display.flip()

    def main_routine(self, clock=None):
        # print("\n\n======================")
        if clock:                           # dt value can be printed to stdout or passed to data model
            dt = clock.tick(self.frame_rate) / 1000
            self.environment.model["dt"] = dt
            # print(dt)

        self.screen.fill((0, 0, 0))        # screen is set to black and passed to environment's main method
        self.environment.main(
            self.screen
        )

        t = self.environment.transition
        e = self.environment.event

        if t:
            self.change_environment(t, e)

    def change_environment(self, file_name, event):
        controllers = [c.name for c in self.environment.controllers]
        env = Environment(file_name, *controllers)

        if not event.get("to_parent", False):
            env.return_env = self.environment.name

        self.environment = env

        if "return_value" in event:
            env.model["_return"] = event["return_value"]


if __name__ == "__main__":
    game = Game(
        pygame.display.set_mode(SCREEN_SIZE),
        FRAME_RATE,
        Environment(START_ENV, *START_CONTROLLERS)
    )

    while True:
        game.main()

