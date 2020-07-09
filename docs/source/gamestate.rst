GameState
----------------------

The GameState represents the current state of the game as a snapshot in time. It's your primary way to view what's happening in the game, holding all the information about the game that you probably care about including things like:

* Current frame count
* Current stage

Also a list of PlayerState objects that represent the state of the 4 players:

* Character X,Y coordinates
* Animation of each character
* Which frame of the animation the character is in

The GameState object should be treated as immutable. Changing it won't have any effect on the game, and you'll receive a new copy each frame anyway.

Design Note
===========

Libmelee tries to create a sensible and intuitive API for Melee. So it may break with some low-level binary structures that the game creates. Some examples:

* Melee is wildly inconsistent with whether animations start at 0 or 1. For some animations, the first frame is 0, for others the first frame is 1. This is very annoying when trying to program a bot. So libmelee re-indexes all animations to start at 1. This way the math is always simple and consistent. IE: If grab comes out on "frame 7", you can reliably check ``character.animation_frame == 7``.
* Libmelee treats Sheik and Zelda as one character that transforms back and forth. This is actually not how the game stores the characters internally, though. Internally to Melee, Sheik and Zelda are the same as Ice Clibmers: there's always two of them. One just happens to be invisible and intangible at a time. But dealing with that would be a pain.

Some Oddities
=============

Other values in Melee are unintuitive, but are a core aspect of how the game works so we can't abstract it away.

* Melee doesn't have just two velocity values (X, Y) it has five! In particular, the game tracks separately your speed "due to being hit" versus "self-induced" speed. This is why after an Amsah tech, you can still go flying off stage. Because your "attack based speed" was high despite not moving anywhere for a while. Libmelee *could* produce a single X,Y speed pair but this would not accurately represent the game state. (For example, SmashBot fails at tech chasing without these 5 speed values)
* Melee tracks whether or not you're "on ground" separately from your character's Y position. It's entirely possible to be "in the air" but be below the stage, and also possible to be "on ground" but have a positive Y value. This is just how the game works and we can't easily abstract this away.
* Your character model can be in a position very different from the X, Y coordinates. A great example of this is Marth's Forward Smash. Marth leans WAAAAY forward when doing this attack, but his X position never actually changes. This is why Marth can smash off the stage and be "standing" on empty air in the middle of it. (Because the game never actually moves Marth's position forward)

.. automodule:: melee.gamestate
   :members:
   :undoc-members:
