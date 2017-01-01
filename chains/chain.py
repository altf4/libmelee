from abc import ABCMeta, abstractmethod

class Chain:

    def __init__(self, gamestate, controller):
        self.gamestate = gamestate
        self.controller = controller

    @abstractmethod
    def pressbuttons(self):
        pass
