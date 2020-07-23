"""Open API written in Python for making your own Smash Bros: Melee AI
Python3 only
Works on Linux/OSX/Windows
"""
from melee.console import Console
from melee.logger import Logger
from melee.gamestate import GameState
from melee.enums import *
from melee.controller import Controller, ControllerState
from melee.framedata import FrameData
from melee.menuhelper import MenuHelper
from melee import menuhelper, techskill, framedata, stages
import melee.version
