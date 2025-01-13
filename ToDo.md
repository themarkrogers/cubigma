# Future Plans

See if there is a way to make the cipher ever encode a letter as itself (a weakness in the enigma machine)

Consider:
* Instead of (or in addition to) changing the chosen corners, maybe rotate slices of the cuboid?
  * Rotation only works if the cuboid is a perfect cube
  * Three parts of the key phrase, three axes of rotation. So, we need an algorithm that Takes the key third and the
    text being encoded/decoded and deterministically chooses which "slice" of the prism to rotate, and which way.
    Maybe: Combine these three elements: The sum of ord() of the key phrase, of the decoded string, and of the encoded
    quartet. This will yield the same three numbers both encoding/decoding (e.g. val = (clear ^ key) - encrypted).
    With this number, we determine which slice (e.g. val % key third % SIZE_OF_AXIS). We always turn it the same way
    (e.g. val % key third % 2). As long as we encode and decode in the same order, we'll be modifying the same
    starting cuboid in the same ways, allowing us to always get the correct opposite corners for decoding.

Convert this project to Rust?

Convert this project to Javascript and run it in the browser?

Maybe, instead of encoding quartets, we use a queue of 4 characters, so that the last char has been encoded 4 times

## User Interface

Make a UI that looks like an Enigma machine in a box
* Instead of a keyboard, but a text field
  * Maybe: Show a keyboard with a key for every symbol in the cuboids 
* Instead of a lamp board, but a mock LCD Screen with a copy button
* Instead of Rotors, visualize cuboids with symbols
* Instead of a Plugboard, put 4 sliders (x, y, z, & num_rotors)
* Put the key phrase input above the rotors
* After encoding a phrase, encourage the user to re-encode the phrase again
