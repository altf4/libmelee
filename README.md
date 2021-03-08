# libmelee
Open API written in Python 3 for making your own Smash Bros: Melee AI that works with Slippi Online

## Installing Libmelee
Libmelee is on pip, this will be the easiest way to get the library and stay updated.

`pip3 install melee`

And definitely stay updated, as the library will be actively improved.

`pip3 install --upgrade melee`

## Setup Instructions

Linux / OSX / Windows

1. Install and configure Slippi, just like you would for rollback netplay. Full instructions here: https://slippi.gg

2. If you're on Linux using the official appimage, extract it using `./Slippi_Online-x86_64.AppImage --appimage-extract`. This will pull apart the app image into a folder in the same directory.

3. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI. Or alternatively the HitBox adapter works well too: https://www.hitboxarcade.com/products/gamecube-controller-adapter

4. Install some custom Slippi Gecko Codes. You can find them here: https://github.com/altf4/slippi-ssbm-asm/blob/libmelee/Output/Netplay/GALE01r2.ini Simply replace your existing `GALE01r2.ini` file with this one. On Linux with the appimage, the file is located at `squashfs-root/usr/bin/Sys/GameSettings/GALE01r2.ini`.  

5. Make sure you have all the `Required` and `Recommended` Gecko Codes enabled.

6. Run `./example.py -e PATH_TO_SLIPPI_FOLDER` (Not the exe itself, the folder) If you're using the Linux appimage, set this to `squashfs-root/usr/bin/`.

## Playing Online

*Do not play on Unranked* There is no libmelee option for it, but don't try. Eventually we'll have a way to register an account as a "bot account" that others will have the ability to opt in or out of playing against. But we don't have it yet. Until then, do not play any bots on Unranked. If you do, we'll know about it, ban your account, overcook all of your food, and seed you against a campy Luigi every tournament. Don't do it.

## Quickstart Video

Here's a ~10 minute video that will show you how easy it can be to write a Melee AI from scratch.
[![Libmelee Quickstart Video](https://img.youtube.com/vi/1R723AS1P-0/hqdefault.jpg)](https://www.youtube.com/watch?v=1R723AS1P-0)

Some of the minor aspects of the API have changed since this video was made, but it's still a good resource.

## The API

This readme will give you a very high level overview of the API. For a more detailed view into specific functions and their params, check out the ReadTheDocs page here: https://libmelee.readthedocs.io/

## GameState
The GameState represents the current state of the game as a snapshot in time. It's your primary way to view what's happening in the game, holding all the information about the game that you probably care about including things like:
- Current frame count
- Current stage

Also a list of PlayerState objects that represent the state of the 4 players:
- Character X,Y coordinates
- Animation of each character
- Which frame of the animation the character is in

The GameState object should be treated as immutable. Changing it won't have any effect on the game, and you'll receive a new copy each frame anyway.

### Note About Consistency and Binary Compatibility
Libmelee tries to create a sensible and intuitive API for Melee. So it may break with some low-level binary structures that the game creates. Some examples:
- Melee is wildly inconsistent with whether animations start at 0 or 1. For some animations, the first frame is 0, for others the first frame is 1. This is very annoying when trying to program a bot. So libmelee re-indexes all animations to start at 1. This way the math is always simple and consistent. IE: If grab comes out on "frame 7", you can reliably check `character.animation_frame == 7`.
- Libmelee treats Sheik and Zelda as one character that transforms back and forth. This is actually not how the game stores the characters internally, though. Internally to Melee, Sheik and Zelda are the same as Ice Climbers: there's always two of them. One just happens to be invisible and intangible at a time. But dealing with that would be a pain.

### Some Values are Unintuitive but Unavoidable
Other values in Melee are unintuitive, but are a core aspect of how the game works so we can't abstract it away.
- Melee doesn't have just two velocity values (X, Y) it has five! In particular, the game tracks separately your speed "due to being hit" versus "self-induced" speed. This is why after an Amsah tech, you can still go flying off stage. Because your "attack based speed" was high despite not moving anywhere for a while. Libmelee *could* produce a single X,Y speed pair but this would not accurately represent the game state. (For example, SmashBot fails at tech chasing without these 5 speed values)
- Melee tracks whether or not you're "on ground" separately from your character's Y position. It's entirely possible to be "in the air" but be below the stage, and also possible to be "on ground" but have a positive Y value. This is just how the game works and we can't easily abstract this away.
- Your character model can be in a position very different from the X, Y coordinates. A great example of this is Marth's Forward Smash. Marth leans WAAAAY forward when doing this attack, but his X position never actually changes. This is why Marth can smash off the stage and be "standing" on empty air in the middle of it. (Because the game never actually moves Marth's position forward)

## Controller
Libmelee lets you programatically press buttons on a virtual controller via Dolphin's named pipes input mechanism. The interface for this is pretty simple, after setting up a controller and connecting it, you can:

`controller.press_button(melee.enums.BUTTON_A)`

or

`controller.release_button(melee.enums.BUTTON_A)`

Or tilt one of the analog sticks by:

`controller.tilt_analog(melee.enums.BUTTON_MAIN, X, Y)`

(X and Y are numbers between 0->1. Where 0 is left/down and 1 is right/up. 0.5 is neutral)

### Note on Controller Input
Dolphin will accept whatever your last button input was each frame. So if you press A, and then release A on the same frame, only the last action will matter and A will never be seen as pressed to the game.

Also, if you don't press a button, Dolphin will just use whatever you pressed last frame. So for example, if on frame 1 you press A, and on frame 2 you press Y, both A and Y will be pressed. The controller does not release buttons for you between frames. Though there is a helper function:

`controller.release_all()`

which will release all buttons and set all sticks / shoulders to neutral.

### API Changes
Each of these old values will be removed in version 1.0.0. So update your programs!
1. `gamestate.player` has been changed to `gamestate.players` (plural) to be more Pythonic.
2. `gamestate.x` and `gamestate.y` have been combined into a named tuple: `gamestate.position`. So you can now access it via `gamestate.position.x`.
3. `projectile.x` and `projectile.y` have been combined into a named tuple: `projectile.position`. So you can now access it via `projectile.position.x`.
4. `projectile.x_speed` and `projectile.y_speed` have been combined into a named tuple: `projectile.speed`. So you can now access it via `projectile.speed.x`
5. `gamestate.stage_select_cursor_x` and `gamestate.stage_select_cursor_x` have both been combined into the PlayerState `cursor`. It makes the API cleaner to just have cursor be separate for each player, even though it's a shared cursor there.
6. `playerstate.character_selected` has been combined into `playerstate.charcter`. Just use the menu to know the context.
7. `playerstate.ecb_left` and the rest have been combined into named tuples like: `playerstate.ecb.left.x` for each of `left`, `right`, `top`, `bottom`. And `x`, `y` coords.
8. `hitlag` boolean has been changed to `hitlag_left` int

## OpenAI Gym
libmelee is inspired by, but not exactly conforming to, the OpenAI Gym API.
