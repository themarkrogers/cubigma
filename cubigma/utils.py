""" Useful shared utilities for the cubigma project. """

from pathlib import Path
from typing import Any
import argparse
import json
import hashlib
import os
import random

import regex

LENGTH_OF_QUARTET = 4
NOISE_SYMBOL = ""


def strengthen_key(key_phrase: str, salt: bytes = None, iterations: int = 100_000, key_length: int = 32) -> tuple[bytes, bytes]:
    """
    Strengthen a user-provided key using Argon2 key derivation.

    Args:
        key_phrase (str): The weak key phrase provided by the user.
        salt (bytes): Optional salt. If None, generates a random 16-byte salt.
        iterations (int): Number of iterations for PBKDF2 (default is 100,000).
        key_length (int): The desired length of the derived key in bytes (default is 32 bytes for 256-bit key).

    Returns:
        bytes: A securely derived key & the salt used
    """
    # Use a secure random salt if not provided
    if salt is None:
        salt = os.urandom(16)

    # Derive the key
    key_phrase_bytes = key_phrase.encode('utf-8')
    key = hashlib.pbkdf2_hmac(
        'sha256',
        key_phrase_bytes,
        salt,
        iterations,
        dklen=key_length  # Derived key length
    )
    return key, salt


def generate_reflector(sanitized_key_phrase: str, num_quartets: int = -1) -> dict[int, int]:
    """
    Generate a deterministic, key-dependent reflector for quartets.

    Args:
        sanitized_key_phrase (str): The encryption key used to seed the random generator.
        num_quartets (int): The total number of unique quartets.

    Returns:
        dict: A mapping of quartets to their reflected counterparts.
    """
    # Create a list of all possible quartets
    quartets = list(range(num_quartets))

    # Seed the random generator with the key
    random.seed(sanitized_key_phrase)

    # Shuffle the quartets
    random.shuffle(quartets)

    # Create pairs and map them bidirectionally
    reflector = {}
    for i in range(0, len(quartets), 2):
        q1, q2 = quartets[i], quartets[i + 1]
        reflector[q1] = q2
        reflector[q2] = q1
    return reflector


def _move_letter_to_front(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """
    Promote a given symbol within a 3D array of characters (playfair_cuboid) by removing it from its
    current position and pushing it to the first position in the first row, while cascading other
    elements down to fill the resulting gaps.

    Args:
        symbol_to_move (str): The ASCII character to promote to the top-left.
        playfair_cuboid (list[list[list[str]]]): The playfair cuboid before moving the requested symbol to the front

    Returns:
        list[list[list[str]]]: The modified playfair cuboid, after moving the symbol requested to the front
    """
    assert playfair_cuboid, "Playfair cuboid not prepared yet!"
    # Find the location of the symbol_to_promote
    found = False
    frame_index = -1
    row_index = -1
    for frame_index, frame in enumerate(playfair_cuboid):
        for row_index, row in enumerate(frame):
            if symbol_to_move in row:
                col_index = row.index(symbol_to_move)
                row.pop(col_index)  # Remove the symbol from its current position
                frame[row_index] = row
                playfair_cuboid[frame_index] = frame
                found = True
                break
        if found:
            break

    if not found:
        raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cuboid.")

    num_blocks = len(playfair_cuboid)
    lines_per_block = len(playfair_cuboid[0])
    # symbols_per_line = len(playfair_cuboid[0][0])

    # Cascade the "hole" to the front
    char_to_move = ""
    did_finish_moving_chars = False
    for frame_idx in range(0, num_blocks):
        cur_frame = playfair_cuboid[frame_idx]
        for row_idx in range(0, lines_per_block):
            cur_row = cur_frame[row_idx]
            if frame_idx == frame_index and row_idx == row_index:
                # Add the char onto this row
                if char_to_move:
                    new_row = [char_to_move] + cur_row
                else:
                    new_row = cur_row
                new_frame = cur_frame
                new_frame[row_idx] = new_row
                playfair_cuboid[frame_idx] = new_frame
                did_finish_moving_chars = True
                break
            # Push the chars off the end of this row
            if char_to_move:
                new_row = [char_to_move] + cur_row[0:-1]
            else:
                new_row = cur_row[0:-1]
            char_to_move = cur_row[-1]
            new_frame = cur_frame
            new_frame[row_idx] = new_row
            playfair_cuboid[frame_idx] = new_frame
        if did_finish_moving_chars:
            break

    # Add symbol to front
    first_frame = playfair_cuboid[0]
    first_row = first_frame[0]
    new_first_row = [symbol_to_move] + first_row
    new_first_frame = first_frame
    new_first_frame[0] = new_first_row
    playfair_cuboid[0] = new_first_frame
    return playfair_cuboid


def prepare_cuboid_with_key_phrase(key_phrase: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """
    Read the cuboid from disk and reorder it according to the key phrase provided

    Args:
        key_phrase (str): Key phrase to use for encrypting/decrypting
        playfair_cuboid (list[list[list[str]]]): The playfair cuboid before the full key phrase has been pulled to the front

    Returns:
        list[list[list[str]]]: The playfair cuboid with full key phrase has been pulled to the front
    """
    assert len(key_phrase) >= 3, "Key phrase must be at least 3 characters long"
    sanitized_key_phrase = remove_duplicate_letters(key_phrase)
    reversed_key = list(reversed(sanitized_key_phrase))
    for key_letter in reversed_key:
        playfair_cuboid = _move_letter_to_front(key_letter, playfair_cuboid)

    # ToDo: This increases the complexity derived from the key
    #   * Maybe: Rotate the slices in a manner based on the key
    #   * Maybe: Change which corner of the cuboid is chosen
    #   * Maybe: both?
    # Split the key phrase into rough thirds. Come up with a logic that converts the string into an algorithm for rotation.
    # Three parts of the key phrase, three axes of rotation. So, we need an algorithm that Takes the key third and the text
    # being encoded/decoded and deterministically chooses which "slice" of the prism to rotate, and which way.
    # Maybe: Combine these three elements: The sum of ord() of the key phrase, of the decoded string, and of the encoded
    # quartet. This will yield the same three numbers both encoding/decoding (e.g. val = (clear ^ key) - encrypted). With
    # this number, we determine which slice (e.g. val % key third % SIZE_OF_AXIS). We always turn it the same way (e.g.
    # val % key third % 2). As long as we encode and decode in the same order, we'll be modifying the same starting cuboid
    # in the same ways, allowing us to always get the correct opposite corners for decoding.

    # ToDo: See if there is a way to make the cipher ever encode a letter as itself (a weakness in the enigma machine)
    return playfair_cuboid


def _move_letter_to_center(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """
    Move a given symbol within a 3D array of characters (playfair_cuboid) by removing it from its
    current position and pushing it to the center of the cuboid, while cascading other elements up to fill the resulting
    gaps.

    Args:
        symbol_to_move (str): The ASCII character to promote to the top-left.
        playfair_cuboid (list[list[list[str]]]): The playfair cuboid before moving the requested symbol to the center

    Returns:
        list[list[list[str]]]: The modified playfair cuboid, after moving the symbol requested to the center
    """
    # Find the location of the symbol_to_promote
    found = False
    frame_index = -1
    row_index = -1
    for frame_index, frame in enumerate(playfair_cuboid):
        for row_index, row in enumerate(frame):
            if symbol_to_move in row:
                col_index = row.index(symbol_to_move)
                row.pop(col_index)  # Remove the symbol from its current position
                frame[row_index] = row
                playfair_cuboid[frame_index] = frame
                found = True
                break
        if found:
            break

    if not found:
        raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cuboid.")

    num_blocks = len(playfair_cuboid)
    lines_per_block = len(playfair_cuboid[0])
    symbols_per_line = len(playfair_cuboid[0][0])

    center_x = num_blocks // 2
    center_y = lines_per_block // 2
    center_z = symbols_per_line // 2

    # Cascade the "hole" to the center
    char_to_move = ""
    did_finish_moving_chars = False
    for frame_idx in reversed(range(0, center_x)):
        cur_frame = playfair_cuboid[frame_idx]
        for row_idx in reversed(range(0, center_y)):
            cur_row = cur_frame[row_idx]
            if frame_idx == frame_index and row_idx == row_index:
                # Add the char onto this row
                if char_to_move:
                    cur_row.insert(center_z, char_to_move)
                new_row = cur_row
                new_frame = cur_frame
                new_frame[row_idx] = new_row
                playfair_cuboid[frame_idx] = new_frame
                did_finish_moving_chars = True
                break
            # Push the chars off the end of this row
            if char_to_move:
                new_row = cur_row[1:] + [char_to_move]
            else:
                new_row = cur_row[1:]
            char_to_move = cur_row[0]
            new_frame = cur_frame
            new_frame[row_idx] = new_row
            playfair_cuboid[frame_idx] = new_frame
        if did_finish_moving_chars:
            break

    # Add symbol to center
    center_frame = playfair_cuboid[center_x]
    center_row = center_frame[center_y]
    center_row.insert(center_z, symbol_to_move)
    new_center_row = center_row
    new_center_frame = center_frame
    new_center_frame[center_y] = new_center_row
    playfair_cuboid[center_x] = new_center_frame
    return playfair_cuboid


def _split_key_into_parts(sanitized_key_phrase: str, num_rotors: int = 3) -> list[str]:
    key_third_length = len(sanitized_key_phrase) // num_rotors
    key_parts = []
    for i in range(num_rotors):
        idx_start = key_third_length * i
        idx_end = key_third_length * (i + 1)
        key_part = sanitized_key_phrase[idx_start:idx_end]
        key_parts.append(key_part)
    return key_parts


def generate_rotors(sanitized_key_phrase: str, prepared_playfair_cuboid: list[list[list[str]]], num_rotors: int = 3) -> list[list[list[list[str]]]]:
    """
    Generate a deterministic, key-dependent reflector for quartets.

    Args:
        sanitized_key_phrase (str): The encryption key used to seed the random generator.
        prepared_playfair_cuboid (list[list[list[str]]]): The playfair cuboid with the full key phrase pulled to the front
        num_rotors (int): Number of "rotors" to use

    Returns:
        list[list[list[list[str]]]]: A list of three "rotors", where each "rotor" is a 3-dimensional cuboid representing
          a playfair cuboid. These are each unique, and each based on the key_phrase provided
    """
    # Seed the random generator with the key
    random.seed(sanitized_key_phrase)

    raw_rotors = []
    for i in range(num_rotors):
        raw_rotor = prepared_playfair_cuboid.copy()
        raw_rotors.append(raw_rotor)

    key_parts = _split_key_into_parts(sanitized_key_phrase, num_rotors=num_rotors)
    finished_rotors = []
    for rotor_num, key_part in enumerate(key_parts):
        cur_rotor = raw_rotors[rotor_num]
        for symbol in key_part:
            cur_rotor = _move_letter_to_center(symbol, cur_rotor)
        finished_rotors[rotor_num] = cur_rotor
    return finished_rotors


def get_opposite_corners(
    point_one: tuple[int, int, int],
    point_two: tuple[int, int, int],
    point_three: tuple[int, int, int],
    point_four: tuple[int, int, int],
        num_blocks: int, lines_per_block: int, symbols_per_line: int
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """
    Given four corners of a rectangular cuboid, find the other four corners.

    Args:
        point_one: A tuple representing the first point (x, y, z).
        point_two: A tuple representing the second point (x, y, z).
        point_three: A tuple representing the third point (x, y, z).
        point_four: A tuple representing the fourth point (x, y, z).
        num_blocks (int): How tall in the cuboid (x).
        lines_per_block (int): How long in the cuboid (y).
        symbols_per_line (int): How wide in the cuboid (z).

    Returns:
        A tuple of four tuples, each representing the coordinates of the remaining corners.
    """
    # Check for unique points
    points = {point_one, point_two, point_three, point_four}
    if len(points) != LENGTH_OF_QUARTET:
        raise ValueError("The provided points must be unique and represent adjacent corners of a rectangular cuboid.")

    x1, y1, z1 = point_one
    x2, y2, z2 = point_two
    x3, y3, z3 = point_three
    x4, y4, z4 = point_four

    max_frame_idx = num_blocks - 1
    max_row_idx = lines_per_block - 1
    max_col_idx = symbols_per_line - 1

    point_five = (max_frame_idx - x1, max_row_idx - y1, max_col_idx - z1)
    point_six = (max_frame_idx - x2, max_row_idx - y2, max_col_idx - z2)
    point_seven = (max_frame_idx - x3, max_row_idx - y3, max_col_idx - z3)
    point_eight = (max_frame_idx - x4, max_row_idx - y4, max_col_idx - z4)

    # ToDo: This is where some of the Enigma logic will happen.
    #  * Use each key third as a "dial". Combine all three dials and a reflector.
    #  * Use these data, and the index of the quartet to drive a deterministic movement in which corners are chosen
    #  * This is also where we can theoretically allow cornerN to be encoded as cornerN (fixing an Enigma issue)
    #  * Open questions:
    #    * How do we reduce the key thirds to a small numeric space?
    #    * What is the deterministic algorithm by which we can drive the movement of the chosen corners?

    # ToDo: Build an machine that, like the Enigma, has 3 "confusion dials" and 1 "reflector"
    #  * Make a playfair_cube out of the whole key_phrase, then make 3 total copies of it, and
    #  * Move the key third from the front to the middle
    #  * Come up with some playfair_cube way of connecting "letter pairs"
    #  * This would accomplish the potentially duplicated letter issue without needing different corners, I think

    # ToDo: Maybe, instead of encoding quartets, we use a queue of 4 characters, so that the last char has been encoded
    #  4 times



    return point_five, point_six, point_seven, point_eight


def get_prefix_order_number_quartet(order_number: int) -> str:
    order_number_str = str(order_number)
    assert len(order_number_str) == 1, "Invalid order number"
    pad_symbols = ["", "", "", order_number_str]
    random.shuffle(pad_symbols)
    return "".join(pad_symbols)


def pad_chunk_with_rand_pad_symbols(chunk: str) -> str:
    pad_symbols = ["", "", ""]
    max_pad_idx = len(pad_symbols) - 1
    while len(chunk) < LENGTH_OF_QUARTET:
        new_random_number = random.randint(0, max_pad_idx)
        random_pad_symbol = pad_symbols[new_random_number]
        if random_pad_symbol not in chunk:
            chunk += random_pad_symbol
    return chunk


def parse_arguments() -> tuple[str, str, str]:
    """
    Parses runtime arguments or prompts the user for input interactively.

    Returns:
        tuple[str, str, str]: A tuple containing key_phrase, mode ('encrypt' or 'decrypt'), and the message.
    """
    parser = argparse.ArgumentParser(description="Encrypt or decrypt a message using a key phrase.")
    parser.add_argument("key_phrase", type=str, help="The key phrase for encryption/decryption.")
    parser.add_argument("--clear_text_message", type=str, help="The plaintext message to encrypt.")
    parser.add_argument("--encrypted_message", type=str, help="The encrypted message to decrypt.")

    args = parser.parse_args()

    if not args.clear_text_message and not args.encrypted_message:
        print("No runtime arguments provided. Switching to interactive mode.")
        mode = input("Are you encrypting or decrypting? (encrypt/decrypt/both): ").strip().lower()
        while mode not in {"encrypt", "decrypt", "both"}:
            mode = input("Invalid choice. Please enter 'encrypt', 'decrypt', or 'both': ").strip().lower()

        key_phrase = input("Enter your key phrase: ").strip()
        if mode in ("encrypt" , "both"):
            message = input("Enter your plaintext message: ").strip()
        else:
            message = input("Enter your encrypted message: ").strip()

        return key_phrase, mode, message

    if args.clear_text_message and args.encrypted_message:
        parser.error("Provide only one of --clear_text_message or --encrypted_message, not both.")

    key_phrase = args.key_phrase
    if args.clear_text_message:
        return key_phrase, "encrypt", args.clear_text_message
    return key_phrase, "decrypt", args.encrypted_message


def prep_string_for_encrypting(orig_message: str) -> str:
    """
    Pad the string with random pad symbols until its length is a multiple of 4

    Args:
        orig_message (str): String to be prepared for encryption

    Returns:
        str: String prepared for encryption
    """
    sanitized_string = ""
    cur_chunk = ""
    chunk_idx = 0
    for orig_char in orig_message:
        if chunk_idx >= LENGTH_OF_QUARTET:
            sanitized_string += cur_chunk
            cur_chunk = ""
            chunk_idx = 0
        if orig_char in cur_chunk:
            cur_chunk = pad_chunk_with_rand_pad_symbols(cur_chunk)
            sanitized_string += cur_chunk
            cur_chunk = ""
            chunk_idx = 0
        cur_chunk += orig_char
        chunk_idx += 1
    sanitized_string += cur_chunk
    return sanitized_string


def read_config(config_file: str = "config.json") -> dict[str, Any]:
    """
    Reads and parses the configuration from the specified JSON file.

    Args:
        config_file (str): The path to the configuration file. Defaults to "config.json".

    Returns:
        dict[str, Any]: The configuration data as a dictionary.
    """
    config_path = Path(config_file)
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def remove_duplicate_letters(orig: str) -> str:
    unique_letters = []
    for letter in orig:
        if letter not in unique_letters:
            unique_letters.append(letter)
    return "".join(list(unique_letters))


def sanitize(raw_input: str) -> str:
    if raw_input.startswith("\\"):
        return raw_input.strip().replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return raw_input.replace("\n", "")


def user_perceived_length(s: str) -> int:
    """
    Used to count the length of strings with surrogate pair emojis

    Args:
        s (str): the string (containing emojis) that needs to be counted

    Returns:
        int: the number of symbols as they would be counted by a human
    """
    # Match grapheme clusters
    graphemes = regex.findall(r"\X", s)
    return len(graphemes)
