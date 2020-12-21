#!/usr/bin/python3
import unittest
import sys
import melee

DOLPHIN_PATH = "path"
ISO_PATH = "another_path"

class DolphinTest(unittest.TestCase):
    """
    Test cases that cannot be run automatically in the Github cloud environment
    Involves running Dolphin and Melee
    """

    def test_character_select(self):
        """
        Start up the console and select our charcter
        """
        console = melee.Console(path=DOLPHIN_PATH, slippi_port=12345)
        controller = melee.Controller(console=console,
                                      port=1,
                                      type=melee.ControllerType.STANDARD)
        console.run(iso_path=ISO_PATH)
        self.assertTrue(console.connect())
        self.assertTrue(controller.connect())

        first_frame = True
        while True:
            gamestate = console.step()
            if first_frame:
                self.assertEqual(gamestate.frame, 0)
                first_frame = False

            if gamestate.menu_state == melee.enums.Menu.IN_GAME:
                pass
            else:
                melee.MenuHelper.menu_helper_simple(gamestate,
                                                    controller,
                                                    melee.Character.FOX,
                                                    melee.Stage.BATTLEFIELD,
                                                    "",
                                                    costume=1,
                                                    autostart=False,
                                                    swag=False)
                if gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT and (gamestate.frame > 30):
                    self.assertEqual(gamestate.players[1].character, melee.Character.FOX)
                    break
        console.stop()

    def test_two_controllers_in_game(self):
        """
        Two controllers, get into game
        """
        console = melee.Console(path=DOLPHIN_PATH, slippi_port=23456)
        controller_one = melee.Controller(console=console,
                                      port=1,
                                      type=melee.ControllerType.STANDARD)
        controller_two = melee.Controller(console=console,
                                      port=2,
                                      type=melee.ControllerType.STANDARD)

        console.run(iso_path=ISO_PATH)
        self.assertTrue(console.connect())
        self.assertTrue(controller_one.connect())
        self.assertTrue(controller_two.connect())

        first_frame = True
        while True:
            gamestate = console.step()
            if first_frame:
                self.assertEqual(gamestate.frame, 0)
                first_frame = False

            if gamestate.menu_state == melee.enums.Menu.IN_GAME:
                if gamestate.frame == -123:
                    self.assertEqual(gamestate.players[1].character, melee.Character.FOX)
                    self.assertEqual(gamestate.players[2].character, melee.Character.MARTH)
                    self.assertEqual(gamestate.stage, melee.Stage.FINAL_DESTINATION)

                elif gamestate.frame == 20:
                    # Do a shine
                    controller_one.press_button(melee.Button.BUTTON_B)
                    controller_one.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
                    # Dash forward (left)
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 0, 0.5)
                elif gamestate.frame == 21:
                    self.assertEqual(gamestate.players[1].action, melee.Action.DOWN_B_GROUND_START)
                    self.assertEqual(gamestate.players[1].action_frame, 1)
                    self.assertEqual(gamestate.players[2].action, melee.Action.DASHING)
                    self.assertEqual(gamestate.players[2].action_frame, 1)
                    self.assertTrue(gamestate.players[2].moonwalkwarning)
                    controller_one.release_all()
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 0.2, 0.5)
                elif gamestate.frame == 22:
                    # self.assertAlmostEqual(gamestate.players[2].controller_state.main_stick[0], 0.018750011920928955)
                    controller_one.release_all()
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0.5)
                elif gamestate.frame == 23:
                    controller_one.release_all()
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 0.7, 0.5)
                elif gamestate.frame == 24:
                    controller_one.release_all()
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 1, 0.5)
                elif gamestate.frame == 25:
                    controller_one.release_all()
                    controller_two.tilt_analog(melee.Button.BUTTON_MAIN, 0, 0.5)
                elif gamestate.frame == 35:
                    # Last frame of pivot turn
                    self.assertEqual(gamestate.players[2].action, melee.Action.TURNING)
                    controller_one.release_all()
                    controller_two.release_all()
                elif gamestate.frame == 36:
                    # This is the first frame of standing after the pivot turn
                    self.assertEqual(gamestate.players[2].action, melee.Action.STANDING)
                    controller_one.release_all()
                    controller_two.press_shoulder(melee.Button.BUTTON_L, 1)
                elif gamestate.frame == 37:
                    controller_one.release_all()
                    controller_two.press_shoulder(melee.Button.BUTTON_L, 0.8)
                elif gamestate.frame == 38:
                    controller_one.release_all()
                    controller_two.press_shoulder(melee.Button.BUTTON_L, 0.3)
                else:
                    controller_one.release_all()
                    controller_two.release_all()
                if gamestate.frame == 60:
                    break
            else:
                melee.MenuHelper.menu_helper_simple(gamestate,
                                                    controller_one,
                                                    melee.Character.FOX,
                                                    melee.Stage.FINAL_DESTINATION,
                                                    "",
                                                    costume=1,
                                                    autostart=True,
                                                    swag=False)
                melee.MenuHelper.menu_helper_simple(gamestate,
                                                    controller_two,
                                                    melee.Character.MARTH,
                                                    melee.Stage.FINAL_DESTINATION,
                                                    "",
                                                    costume=1,
                                                    autostart=False,
                                                    swag=False)
        console.stop()

if __name__ == '__main__':
    assert(len(sys.argv) == 3)
    ISO_PATH = sys.argv.pop()
    DOLPHIN_PATH = sys.argv.pop()
    unittest.main()
