Libmelee
=============

Open API written in Python 3 for making your own Smash Bros: Melee AI that works with Slippi Online

.. toctree::
  :maxdepth: 8

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

  console = melee.Console(path="/SlippiOnline/")

  controller = melee.Controller(console=console, port=1)
  controller_human = melee.Controller(console=console,
                                      port=2,
                                      type=melee.ControllerType.GCN_ADAPTER)

  console.run()
  console.connect()

  controller.connect()
  controller_human.connect()

  while True:
      gamestate = console.step()
      # Press buttons on your controller based on the GameState here!

For a fully fleshed-out example program that you can run, check out ``example.py``.

If you're looking to read SLP files and don't need to interface with Dolphin, then it's even easier:

.. code-block:: python
  :linenos:

  console = melee.Console(is_dolphin=False, path="YOUR_FILE.slp")
  console.connect()

  while True:
      gamestate = console.step()
      # step() returns None when the file ends
      if gamestate is None:
          break
      print(gamestate.player[1].x, gamestate.player[1].y)

Getting Started
--------------------
First thing's first, let's make sure you have everything setup properly.

1. Build the following the Ishiiruka version from source: https://github.com/altf4/Ishiiruka/tree/gamma There is a PR out for this functionality, so hopefully soon you won't need to do this step. The full steps and requirements for building Ishiiruka is outside the scope of this document.
2. Make sure there is an empty text file named ``portable.txt`` adjacent to your ``Dolphin.exe`` or ``dolphin-emu`` binary.
3. Make sure you're running Melee v1.02 NTSC. Other versions will not work.
4. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI Other adapters may work, but setting these up is outside the scope of this document.
5. Install some custom Slippi Gecko Codes. You can find them here: https://github.com/altf4/slippi-ssbm-asm/blob/master/Output/Netplay/GALE01r2.ini Simply replace your existing `GALE01r2.ini` file with this one. There is also a PR out for this functionality, so hopefully you won't need to do this step soon either.
6. Make sure you have all the ``Required`` and ``Recommended`` Gecko Codes enabled.
7. Run ``./example.py -e PATH_TO_DIR_HOLDING_DOLPHIN_EXE``
