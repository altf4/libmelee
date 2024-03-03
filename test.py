#!/usr/bin/python3
import unittest

import melee


class SLPFile(unittest.TestCase):
    """
    Test cases that can be run automatically in the Github cloud environment
    In particular, there are no live dolphin tests here.
    """

    def test_read_file(self):
        """
        Load and parse SLP file
        """
        console = melee.Console(
            system="file",
            allow_old_version=False,
            path="test_artifacts/test_game_1.slp",
        )
        self.assertTrue(console.connect())
        framecount = 0
        while True:
            gamestate = console.step()
            framecount += 1
            if gamestate is None:
                self.assertEqual(framecount, 1039)
                break
            if gamestate.frame == -123:
                self.assertEqual(console.slp_version, "3.6.1")
                self.assertEqual(gamestate.players[1].character.value, 1)
                self.assertEqual(gamestate.players[2].character.value, 1)
            if gamestate.frame == 297:
                self.assertEqual(gamestate.players[1].action.value, 0)
                self.assertEqual(gamestate.players[2].action.value, 27)
                self.assertEqual(gamestate.players[1].percent, 17)
                self.assertEqual(gamestate.players[2].percent, 0)

    def test_read_old_file(self):
        """
        Load and parse old SLP file
        """
        console = melee.Console(
            system="file", allow_old_version=True, path="test_artifacts/test_game_2.slp"
        )
        self.assertTrue(console.connect())
        framecount = 0
        while True:
            gamestate = console.step()
            framecount += 1
            if gamestate is None:
                self.assertEqual(framecount, 3840)
                break
            if gamestate.frame == -123:
                self.assertEqual(console.slp_version, "2.0.1")
                self.assertEqual(gamestate.players[2].character.value, 3)
                self.assertEqual(gamestate.players[3].character.value, 18)
            if gamestate.frame == 301:
                self.assertEqual(gamestate.players[2].action.value, 88)
                self.assertEqual(gamestate.players[3].action.value, 56)
                self.assertEqual(gamestate.players[2].percent, 25)
                self.assertEqual(gamestate.players[3].percent, 0)

    def test_framedata(self):
        """
        Test that frame and stage data retreive correctly
        """
        framedata = melee.FrameData()
        self.assertTrue(framedata.is_attack(melee.Character.FALCO, melee.Action.DAIR))
        self.assertFalse(
            framedata.is_attack(melee.Character.FALCO, melee.Action.STANDING)
        )

    def test_corrupt_file(self):
        """Load a corrupt SLP file and make sure we don't crash"""
        console = melee.Console(
            system="file",
            allow_old_version=True,
            path="test_artifacts/corrupt_game_1.slp",
        )
        self.assertFalse(console.connect())

        console = melee.Console(
            system="file",
            allow_old_version=True,
            path="test_artifacts/corrupt_game_2.slp",
        )
        self.assertFalse(console.connect())

        console = melee.Console(
            system="file",
            allow_old_version=True,
            path="test_artifacts/corrupt_game_3.slp",
        )
        self.assertFalse(console.connect())


if __name__ == "__main__":
    unittest.main()
