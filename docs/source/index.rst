Libmelee
=============

Open API written in Python 3 for making your own Smash Bros: Melee AI that works with Slippi Online

.. toctree::
  :maxdepth: 8

  console
  controller
  gamestate
  menuhelper
  stages
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

1. Install and configure Slippi, just like you would for rollback netplay. Full instructions here: https://slippi.gg
2. If you're on Linux using the official appimage, extract it using `./Slippi_Online-x86_64.AppImage --appimage-extract`. This will pull apart the app image into a folder in the same directory.
3. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI. Or alternatively the HitBox adapter works well too: https://www.hitboxarcade.com/products/gamecube-controller-adapter
4. Install some custom Slippi Gecko Codes. You can find them here: https://github.com/altf4/slippi-ssbm-asm/blob/libmelee/Output/Netplay/GALE01r2.ini Simply replace your existing `GALE01r2.ini` file with this one. On Linux with the appimage, the file is located at `squashfs-root/usr/bin/Sys/GameSettings/GALE01r2.ini`.
5. Make sure you have all the `Required` and `Recommended` Gecko Codes enabled.
6. Run `./example.py -e PATH_TO_SLIPPI_FOLDER` (Not the exe itself, the folder) If you're using the Linux appimage, set this to `squashfs-root/usr/bin/`.
