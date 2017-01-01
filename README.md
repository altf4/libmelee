# libmelee
Open API written in Python for making your own Smash Bros: Melee AI

## Setup Instructions

Linux / OSX only. (Windows coming soon)

1. Install the Dolphin version here:
https://github.com/altf4/dolphin/tree/memorywatcher
This contains an important update to allow Dolphin to be able to read projectile information from Melee. Unfortunately, you'll have to build this from source until they accept my Pull Request:
https://github.com/dolphin-emu/dolphin/pull/4407

2. Make sure you're running Melee v1.02 NTSC. Other versions will not work.

3. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI

4. Install via pip: (or by cloning this repo for the very latest)
`pip3 install melee`

5. Run `example.py`

## NOTE:
The libmelee API should be considered to be in a state of high flux until you stop seeing this message. Expect many changes, including plenty that break compatibility. Just FYI

libmelee is inspired by, but not exactly conforming to, the OpenAI Gym API.
