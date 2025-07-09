# The King of Fighters 2002 UM Input Render
simple input render, developed as a study for how games read inputs from XInput and DirectInput APIs.
the code works without the "sleep" delay function, and the game can read the actions properly, but just it. by adding any delay, it somehows broke the game and makes the game miss a lot of inputs, probably bcuz of the nature of time.sleep function.

the code simulates inputs using pyvjoystick wrapper and vjoy driver, reverse engineering the game and sending the inputs by its offsets is probably a much better way to do it, and will bypass all the problems this code has.

the games needs to be the active window to render the inputs, is a common "security" way to do it, but kof seems to have some more "security input cleaning" mechanisms to render inputs to the game, that im too lazy to go deeper.
