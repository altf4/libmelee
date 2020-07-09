Libmelee
=============

Open API written in Python 3 for making your own Smash Bros: Melee AI that works with Slippi Online

.. toctree::
  :maxdepth: 8

  gettingstarted
  console
  controller
  gamestate
  menuhelper
  framedata
  logger
  enums

Quick Example
--------------------

.. code-block:: python
  :linenos:

  import melee

  console = melee.console.Console(ai_port=1,
                                  is_dolphin=True,
                                  opponent_port=2,
                                  opponent_type=melee.enums.CONTROLLER_HUMAN,
                                  dolphin_executable_path="~/SlippiOnline/"",
                                  slippi_address="127.0.0.1",
                                  logger=None)

  controller = melee.controller.Controller(port=1, console=console)

  console.run()
  console.connect()

  controller.connect()

  while True:
      gamestate = console.step()
      # Press buttons on your controller based on the GameState here!
