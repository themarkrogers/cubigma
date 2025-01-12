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


def _insert_symbol(
    playfair_cuboid: list[list[list[str]]],
    target_frame: int,
    target_row: int,
    target_col: int,
    symbol_to_move: str
):
    """Inserts the symbol into the specified position in the playfair cuboid."""
    playfair_cuboid[target_frame][target_row].insert(target_col, symbol_to_move)


def _move_letter_to_position(
    symbol_to_move: str,
    playfair_cuboid: list[list[list[str]]],
    target_position: tuple[int, int, int],
    direction: str = "to-front"
) -> list[list[list[str]]]:
    """
    Generalized function to move a letter to a specific position in the playfair cuboid.

    Args:
        symbol_to_move (str): The ASCII character to move.
        playfair_cuboid (list[list[list[str]]]): The 3D cuboid to modify.
        target_position (tuple[int, int, int]): The target frame, row, and column to move the symbol to.
        direction (str): The direction to cascade ('to-front' or 'to-back').

    Returns:
        list[list[list[str]]]: The modified playfair cuboid.
    """
    frame_idx, row_idx, col_idx = _find_symbol(symbol_to_move, playfair_cuboid)
    playfair_cuboid[frame_idx][row_idx].pop(col_idx)  # result of pop == symbol_to_move
    _cascade_gap(playfair_cuboid, frame_idx, row_idx, col_idx, direction=direction)
    target_x, target_y, target_z = target_position
    _insert_symbol(playfair_cuboid, target_x, target_y, target_z, symbol_to_move)
    return playfair_cuboid


def _move_letter_to_front(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the front of the playfair cuboid."""
    return _move_letter_to_position(symbol_to_move, playfair_cuboid, (0, 0, 0))


def _move_letter_to_center(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the center of the playfair cuboid."""
    num_blocks = len(playfair_cuboid)
    lines_per_block = len(playfair_cuboid[0])
    symbols_per_line = len(playfair_cuboid[0][0])
    center_position = (num_blocks // 2, lines_per_block // 2, symbols_per_line // 2)
    return _move_letter_to_position(symbol_to_move, playfair_cuboid, center_position)


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


# The below functions are under test


def _cascade_gap(
    playfair_cuboid: list[list[list[str]]],
    start_frame: int,
    start_row: int,
    direction: str = "to-front"
) -> list[list[list[str]]]:
    """
    Cascades the gap caused by removing a symbol, shifting elements to fill the gap.

    Args:
        playfair_cuboid (list[list[list[str]]]): The 3D cuboid to modify.
        start_frame (int): The frame where the gap starts.
        start_row (int): The row within the frame where the gap starts.
        direction (str): The direction to cascade ('to-front' or 'to-back').

    Returns:
        list[list[list[str]]]: Modified 3D cuboid
    """
    char_to_move = ""
    if direction == "to-front":
        range_blocks = range(0, start_frame + 1)  # Push chars from the front into the hole
    elif direction == "to-back":
        range_blocks = reversed(range(start_frame, len(playfair_cuboid)))  # Push chars the back into the hole
    else:
        raise ValueError("direction can only be either 'to-front' or 'to-back'")
    new_cuboid = playfair_cuboid.copy()
    for frame_idx in range_blocks:
        cur_frame = playfair_cuboid[frame_idx].copy()

        if direction == "to-front":
            if frame_idx == start_frame:
                row_limit = start_row + 1
            else:
                row_limit = len(playfair_cuboid[frame_idx])
            range_rows = range(0, row_limit)
        else:
            max_rows_in_frame = len(playfair_cuboid[frame_idx])
            if frame_idx == start_frame:
                row_limit = start_row
            else:
                row_limit = 0
            range_rows =  reversed(range(row_limit, max_rows_in_frame))
        for row_idx in range_rows:
            cur_row = cur_frame[row_idx]
            if char_to_move:
                if direction == "to-front":
                    # Put last popped char at the start of this line, since we're pushing to the back
                    new_row = [char_to_move] + cur_row[:-1]
                else:
                    # Put last popped char at the end of this line, since we're pushing to the front
                    new_row = cur_row[1:] + [char_to_move]
            else:
                if direction == "to-front":
                    # Drop the last char, since we're pushing the hole to the back
                    new_row = cur_row[:-1]
                else:
                    # Drop the first char, since we're pushing the hole to the front
                    new_row = cur_row[1:]
            if direction == "to-front":
                # Grab the last char, since it just got dropped
                char_to_move = cur_row[-1]
            else:
                # Grab the first char, since it just got dropped
                char_to_move = cur_row[0]
            if frame_idx == start_frame and row_idx == start_row:
                if direction == "to-front":
                    # Drop the last char, since we're pushing the hole to the back
                    new_row = new_row + [char_to_move]
                else:
                    # Drop the first char, since we're pushing the hole to the front
                    new_row = [char_to_move] + new_row
            cur_frame[row_idx] = new_row
        new_cuboid[frame_idx] = cur_frame
    return new_cuboid


def _find_symbol(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> tuple[int, int, int]:
    """Finds the frame, row, and column of the given symbol in the playfair cuboid."""
    for frame_idx, frame in enumerate(playfair_cuboid):
        for row_idx, row in enumerate(frame):
            if symbol_to_move in row:
                col_idx = row.index(symbol_to_move)
                return frame_idx, row_idx, col_idx
    raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cuboid.")


def _split_key_into_parts(sanitized_key_phrase: str, num_rotors: int = 3) -> list[str]:
    if len(sanitized_key_phrase) < num_rotors:
        raise ValueError("Message length must be at least the number of rotors")
    if num_rotors <= 0:
        raise ValueError("Invalid number of rotors. Must be at least 1.")
    key_third_length = len(sanitized_key_phrase) // num_rotors
    key_parts = []
    for i in range(num_rotors):
        idx_start = key_third_length * i
        idx_end = key_third_length * (i + 1)
        if i == num_rotors - 1:
            key_part = sanitized_key_phrase[idx_start:]
        else:
            key_part = sanitized_key_phrase[idx_start:idx_end]
        key_parts.append(key_part)
    return key_parts


def get_prefix_order_number_quartet(order_number: int) -> str:
    order_number_str = str(order_number)
    assert len(order_number_str) == 1, "Invalid order number"
    pad_symbols = ["", "", "", order_number_str]
    random.shuffle(pad_symbols)
    return "".join(pad_symbols)


def index_to_quartet(index: int, symbols: list[str]) -> str:
    """
    Convert an index to a quartet based on the provided symbols.

    Args:
        index (int): The index to convert.
        symbols (str): A string containing the unique symbols.

    Returns:
        str: The quartet representing the index.
    """
    if not symbols:
        raise ValueError("List of symbols cannot be None or empty")
    num_symbols = len(symbols)
    if num_symbols < LENGTH_OF_QUARTET:
        raise ValueError("List of symbols must be at least 4")
    a = index // (num_symbols**3)
    b = (index % (num_symbols**3)) // (num_symbols**2)
    c = (index % (num_symbols**2)) // num_symbols
    d = index % num_symbols

    result = f"{symbols[a]}{symbols[b]}{symbols[c]}{symbols[d]}"
    return result


def pad_chunk_with_rand_pad_symbols(chunk: str) -> str:
    if len(chunk) < 1:
        raise ValueError("Chunk cannot be empty")
    pad_symbols = ["", "", ""]
    max_pad_idx = len(pad_symbols) - 1
    while len(chunk) < LENGTH_OF_QUARTET:
        new_random_number = random.randint(0, max_pad_idx)
        random_pad_symbol = pad_symbols[new_random_number]
        if random_pad_symbol not in chunk:
            chunk += random_pad_symbol
    return chunk


def quartet_to_index(quartet: str, symbols: list[str]) -> int:
    """
    Convert a quartet to its corresponding index based on the provided symbols.

    Args:
        quartet (str): The quartet to convert.
        symbols (str): A string containing the unique symbols.

    Returns:
        int: The index representing the quartet.
    """
    num_symbols = len(symbols)
    if user_perceived_length(quartet) != LENGTH_OF_QUARTET:
        raise ValueError("Quartet must be exactly 4 characters long.")
    indices = [symbols.index(char) for char in split_to_human_readable_symbols(quartet)]
    result = (
            indices[0] * (num_symbols ** 3) +
            indices[1] * (num_symbols ** 2) +
            indices[2] * num_symbols +
            indices[3]
    )
    return result


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


def split_to_human_readable_symbols(s: str) -> list[str]:
    """
    Splits a string with a user-perceived length of 4 into its 4 human-discernible symbols.

    Args:
        s (str): The input string, guaranteed to have a user_perceived_length of 4.

    Returns:
        list[str]: A list of 4 human-readable symbols, each as a separate string.
    """
    # Match grapheme clusters (human-discernible symbols)
    graphemes = regex.findall(r"\X", s)
    # Ensure the string has exactly 4 human-discernible symbols
    if len(graphemes) != 4:
        raise ValueError("The input string must have a user-perceived length of 4.")
    return graphemes


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
