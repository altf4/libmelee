"""Open API written in Python for making your own Smash Bros: Melee AI
Python3 only
Works on Linux/OSX/Windows
"""
from melee.console import Console
from melee.logger import Logger
from melee.gamestate import GameState
from melee.enums import Stage, Menu, Character, Button, Action, ProjectileSubtype
from melee.controller import Controller, ControllerState
from melee import menuhelper, techskill, framedata, stages
import melee.version
