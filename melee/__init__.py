"""Open API written in Python for making your own Smash Bros: Melee AI
Python3 only
Currently only works on Linux/OSX
"""
from melee.dolphin import Dolphin
from melee.logger import Logger
from melee.gamestate import GameState
from melee.enums import Stage, Menu, Character, Button, Action, ProjectileSubtype
from melee.controller import Controller, ControllerState
from melee import menuhelper, techskill
import melee.version
