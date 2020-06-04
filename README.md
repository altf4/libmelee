# libmelee
Open API written in Python for making your own Smash Bros: Melee AI

## Console Setup Instructions

1. Get yourself a hacked Wii Slippi setup. Doing so is outside the scope of this document.
Checkout https://slippi.gg.

2. Get yourself a USB Ethernet adapter for your Wii. The Wii has Wi-Fi, but it is not good. It drops out randomly and is super slow. Only ethernet will be fast and reliable enough. Buy this adapter, as not every adapter will work with a Wii:

https://www.amazon.com/UGREEN-Ethernet-Adapter-Nintendo-Chromebook/dp/B00MYT481C/

3. In the Slippi Melee settings, turn `Slippi Networking` to `Yes`.

4. In the Slippi Melee settings, turn `Lag Reduction` to `PD` or `PD+VB`. (VB only works if you have a progressive-scan setup, FYI)

5. (Linux) Add your user to the `dialout` group, so you can access the TAStm32 without root.

`sudo usermod -a -G dialout YOUR_USER_NAME`

## Dolphin Setup Instructions

Linux / OSX only. (Windows coming soon)

1. Install (or build locally) the Ishiiruka version here: https://github.com/altf4/Ishiiruka/tree/beta

2. Make sure you're running Melee v1.02 NTSC. Other versions will not work.

3. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI

4. Install via pip: (or by cloning this repo for the very latest)
`pip3 install melee`

5. Run `example.py` (for an installed version of dolphin, use the -e flag for a local version) `./example.py -e PATH_TO_DIR_HOLDING_DOLPHIN_EXE`

## NOTE:
The libmelee API should be considered to be in a state of high flux until you stop seeing this message. Expect many changes, including plenty that break compatibility. Just FYI

libmelee is inspired by, but not exactly conforming to, the OpenAI Gym API.
