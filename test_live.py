#!/usr/bin/python3
import unittest
import sys
import melee

class DolphinTest(unittest.TestCase):
    """
    Test cases that cannot be run automatically in the Github cloud environment
    Involves running Dolphin and Melee
    """
    DOLPHIN_PATH = "path"

    def test_connect_console(self):
        """
        Start and connect to the console
        """
        console = melee.Console(path=DolphinTest.DOLPHIN_PATH)
        controller = melee.Controller(console=console,
                                      port=1,
                                      type=melee.ControllerType.STANDARD)
        console.run()
        self.assertTrue(console.connect())
        self.assertTrue(controller.connect())

        first_frame = True
        while True:
            gamestate = console.step()
            if first_frame:
                self.assertEqual(gamestate.frame, 0)
                first_frame = False


            melee.MenuHelper.menu_helper_simple(gamestate,
                                                controller,
                                                melee.Character.FOX,
                                                melee.Stage.YOSHIS_STORY,
                                                "",
                                                costume=1,
                                                autostart=False,
                                                swag=False)


if __name__ == '__main__':
    assert(len(sys.argv) == 2)
    DolphinTest.DOLPHIN_PATH = sys.argv.pop()
    unittest.main()
