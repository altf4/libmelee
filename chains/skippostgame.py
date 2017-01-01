from chains import chain
from melee import enums

class SkipPostgame(chain.Chain):

    def pressbuttons(self):
        controller = self.controller

        #Was the start button pressed last frame?
        if controller.prev.button[enums.Button.BUTTON_START] == False:
            controller.press_button(enums.Button.BUTTON_START)
        else:
            controller.release_button(enums.Button.BUTTON_START)
