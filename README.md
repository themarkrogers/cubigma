# Cubigma

[![Unit Tests](https://github.com/themarkrogers/cubigma/actions/workflows/python-app.yml/badge.svg)](https://github.com/themarkrogers/cubigma/actions/workflows/python-app.yml)
[![Project Status](http://opensource.box.com/badges/active.svg)](http://opensource.box.com/badges)

# Introduction

## Encryption

This is an encryption & steganography tool. The encryption algorithm implemented here is a modification to the Playfair 
cipher. Instead of a 2-dimensional square of 25 letters to encode pairs of letters, this algorithm uses a 3-dimensional 
cube of X * Y * Z symbols to encode quartets of symbols. 

Additionally, this algorithm takes inspiration from the Enigma machine and uses the provided key phrase to rotate 
"slices" of the rectangular cuboid of symbols after encoding each quartet (think of making 1 rotation to a Rubik's 
cube). This "rotor stepping" logic also effects which corners of the quartet cuboid are chosen when encoding. 

However, unlike an Enigma machine, this algorithm does allow a letter to occasionally be encoded as itself.

Users can configure the following:
* Volume of the playfair cubes used as rotors
* How many playfair cubes to generate, and how many to use as rotors
  * Historically, 5 rotors came with the Enigma machine and only 3 were used.
* The plugboard ()

| Component         | Enigma                                      | Cubigma                                        |
|-------------------|---------------------------------------------|------------------------------------------------|
| Input             | Keyboard                                    | Runtime argument, user input, or method param  |
| Rotors            | Physical rotors with electrical connections | Software-based rotating Playfair cubes         |
| Rotor Selection   | 5 rotors are available, only 3 are used     | 5 rotors are available, only 3 are used        |
| Stepping          | Predictable rotor stepping                  | Predictable corner rotation & slice rotation   |
| Reflector         | Symmetrical pairwise mapping of letters     | Symmetrical pairwise map of quartets           |
| Plugboard         | Swappable pairs of letters (configurable)   | Swappable pairs of symbols (configurable)      |
| Key Configuration | Rotor order, ring settings, plugboard,      | Key phrase, cube dimension, number of rotors,  |
|                   | initial rotor positions                     | rotor selection, plugboard                     |
| Output            | Lamp board                                  | Printed output or method result                |

## Steganography

This tool also includes a steganography component. This is not a separate tool because the encryption algorithm is 
slightly different when also using the steganography component. Before encryption, the message is inflated with "noise" 
and then divided into 5 differently sized "chunks". Each chunk of the message is then given an order number and 
encrypted using the Cubigma encryption algorithm. Then, each encrypted chunk is hidden in a square of pixels in a 
provided image.  

# How to Use

## Requirements
* Key phrase must be a string of at least 1 character.
* The volume of your cube must be: 101 < V < 1646.
* At least 1 rotor must be used

## Preparation
Agree upon the following with your recipient (these are specified in the `config.yaml` file at the project root):
1. Your shared secret key phrase (must be a string at least 1 symbol long; symbols & emojis are allowed & encouraged)
2. The size of your playfair cubes (default is 7 x 7 x 7; options range from 5 x 5 x 5 to 11 x 11 x 11)
  * The volume of your cube must be: 101 < V < 1646.  
3. How many rotors to generate and how many to use (defaults: 5 are generated, 3 are used. Minimums: 1 & 1)
4. Which rotors will be used (default: 5 are generated, choose any 3 different rotors to use. Minimum: 1)
5. Decide if using simple encryption or encryption+steganography (default: encryption only)

## Encryption Only
1. Prepare your python environment
2. Prepare your `config.yaml` file
3. Prepare your clear text message
4. Run the python code
6. Enter your key phrase
7. Enter your clear text message
8. Send encrypted text to your recipient

## Decryption Only
1. Prepare your python environment
2. Prepare your `config.yaml` file
3. Prepare your encrypted message
4. Run the python code
5. Enter your key phrase
6. Enter your encrypted message
7. Read the clear text message

## Encryption + Steganography
1. Prepare your python environment
2. Prepare your `config.yaml` file
3. Find a (preferably noisy) PNG image
4. Prepare your clear text message
5. Run the python code
6. Enter your key phrase
7. Enter the absolute path to your PNG image
8. Send modified image to your recipient

## Decryption + Steganography
1. Prepare your python environment
2. Prepare your `config.yaml` file
4. Have your image file's filepath ready
5. Run the python code
6. Enter your key phrase
7. Enter the absolute path to your PNG image
8. Read the clear text message


# Notes

ASCII frequency:
* ASCII: https://opendata.stackexchange.com/a/19792
* Emoji: https://home.unicode.org/emoji/emoji-frequency/

# Maintenance

## Unit Tests

`coverage run -m unittest discover`
`coverage report`
`coverage html`

## Linting

```
black .
mypy .
flake8 .
pylint .
```