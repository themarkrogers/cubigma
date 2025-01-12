# Cubigma

# Introduction

This is an encryption & steganography tool. The encryption algorithm implemented here is a modification to the Playfair 
cipher. Instead of a 2-dimensional square of 25 letters to encode pairs of letters, this algorithm uses a 3-dimensional 
rectangular cuboid of X * Y * Z symbols to encode quartets of symbols. 

Additionally, this algorithm takes inspiration from the Enigma machine and uses the provided key phrase to rotate 
"slices" of the rectangular cuboid of symbols after encoding each quartet (think of making 1 rotation to a Rubik's cube). 

However, unlike an Enigma machine, this algorithm does allow a letter to occasionally be encoded as itself.

# How to Use

Requirements:
* Key Phrase must be at least 3 characters long
* The area of your cuboid is not recommended to go below 101 (5*5*5 is a good minimum.).  

Preparation:
1. Agree on a cuboid size with your recipient (default is 7x7x7)
   * If not using the default cuboid size, then modify the three constants in the top of `cubigma.py`
2. Agree on a key phrase with your recipient (in a secure manner)

Encrypting:
1. Find a (preferably noisy) PNG image
2. Prepare your clear text message
3. Run the `encode.sh` file
4. Enter your key phrase
5. Enter the absolute path to your PNG image


# Notes

ASCII frequency:
* ASCII: https://opendata.stackexchange.com/a/19792
* Emoji: https://home.unicode.org/emoji/emoji-frequency/