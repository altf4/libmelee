# libmelee
Open API written in Python for making your own Smash Bros: Melee AI

## Dolphin Setup Instructions

Linux / OSX / Windows

1. Install (or build locally) the Ishiiruka version here: https://github.com/altf4/Ishiiruka/tree/gamma

2. Make sure there is an empty text file named `portable.txt` adjacent to your `Dolphin.exe`.

3. Make sure you're running Melee v1.02 NTSC. Other versions will not work.

4. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI

5. Install come custom Slippi Gecko Codes. You can find them here: https://github.com/altf4/slippi-ssbm-asm/blob/master/Output/Netplay/GALE01r2.ini Simply replace your existing `GALE01r2.ini` file with this one.

6. Make sure you have all the `Required` and `Recommended` Gecko Codes enabled.

7. Run `example.py` (for an installed version of dolphin, use the -e flag for a local version) `./example.py -e PATH_TO_DIR_HOLDING_DOLPHIN_EXE`

## NOTE:
The libmelee API should be considered to be in a state of high flux until you stop seeing this message. Expect many changes, including plenty that break compatibility. Just FYI

libmelee is inspired by, but not exactly conforming to, the OpenAI Gym API.
