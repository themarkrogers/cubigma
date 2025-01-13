""" Useful shared utilities for the cubigma project. """

from pathlib import Path
from typing import Any
import argparse
import json
import hashlib
import numbers
import os
import random

import regex

LENGTH_OF_QUARTET = 4
NOISE_SYMBOL = ""


def prepare_cuboid_with_key_phrase(key_phrase: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """
    Read the cuboid from disk and reorder it according to the key phrase provided

    Args:
        key_phrase (str): Key phrase to use for encrypting/decrypting
        playfair_cuboid (list[list[list[str]]]): The playfair cuboid before the key phrase has been pulled to the front

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
    # Split the key phrase into rough thirds. Come up with a logic that converts the string into an algorithm for
    # rotation.
    # Three parts of the key phrase, three axes of rotation. So, we need an algorithm that Takes the key third and the
    # text being encoded/decoded and deterministically chooses which "slice" of the prism to rotate, and which way.
    # Maybe: Combine these three elements: The sum of ord() of the key phrase, of the decoded string, and of the encoded
    # quartet. This will yield the same three numbers both encoding/decoding (e.g. val = (clear ^ key) - encrypted).
    # With this number, we determine which slice (e.g. val % key third % SIZE_OF_AXIS). We always turn it the same way
    # (e.g. val % key third % 2). As long as we encode and decode in the same order, we'll be modifying the same
    # starting cuboid in the same ways, allowing us to always get the correct opposite corners for decoding.

    # ToDo: See if there is a way to make the cipher ever encode a letter as itself (a weakness in the enigma machine)
    return playfair_cuboid


def _get_opposite_corners(
    point_1: tuple[int, int, int],
    point_2: tuple[int, int, int],
    point_3: tuple[int, int, int],
    point_4: tuple[int, int, int],
    num_blocks: int,
    lines_per_block: int,
    symbols_per_line: int,
    num_quartets_encoded: int
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """
    Given four corners of a rectangular cuboid, find the other four corners.

    Args:
        point_1: A tuple representing the first point (x, y, z).
        point_2: A tuple representing the second point (x, y, z).
        point_3: A tuple representing the third point (x, y, z).
        point_4: A tuple representing the fourth point (x, y, z).
        num_blocks (int): How tall in the cuboid (x).
        lines_per_block (int): How long in the cuboid (y).
        symbols_per_line (int): How wide in the cuboid (z).

    Returns:
        A tuple of four tuples, each representing the coordinates of the remaining corners.
    """
    # Check for unique points
    points = {point_1, point_2, point_3, point_4}
    if len(points) != LENGTH_OF_QUARTET:
        raise ValueError("The provided points must be unique and represent adjacent corners of a rectangular cuboid.")

    x1, y1, z1 = point_1
    x2, y2, z2 = point_2
    x3, y3, z3 = point_3
    x4, y4, z4 = point_4

    max_frame_idx = num_blocks - 1
    max_row_idx = lines_per_block - 1
    max_col_idx = symbols_per_line - 1

    point_5 = (max_frame_idx - x1, max_row_idx - y1, max_col_idx - z1)
    point_6 = (max_frame_idx - x2, max_row_idx - y2, max_col_idx - z2)
    point_7 = (max_frame_idx - x3, max_row_idx - y3, max_col_idx - z3)
    point_8 = (max_frame_idx - x4, max_row_idx - y4, max_col_idx - z4)
    points = [point_1, point_2, point_3, point_4, point_5, point_6, point_7, point_8]

    # ToDo: This is where some of the Enigma logic will happen.
    #  * Use each key third as a "dial". Combine all three dials and a reflector.
    #  * Use these data, and the index of the quartet to drive a deterministic movement in which corners are chosen
    #  * This is also where we can theoretically allow cornerN to be encoded as cornerN (fixing an Enigma issue)
    #  * Open questions:
    #    * How do we reduce the key thirds to a small numeric space?
    #    * What is the deterministic algorithm by which we can drive the movement of the chosen corners?

    indices_to_choose = [4,7,1,4]  # ToDo: How do we reduce the key_phrase into this?
    chosen_point_1 = points[indices_to_choose[0]]
    chosen_point_2 = points[indices_to_choose[1]]
    chosen_point_3 = points[indices_to_choose[2]]
    chosen_point_4 = points[indices_to_choose[3]]

    return chosen_point_1, chosen_point_2, chosen_point_3, chosen_point_4


# The below functions are under test


def _find_symbol(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> tuple[int, int, int]:
    """Finds the frame, row, and column of the given symbol in the playfair cuboid."""
    for frame_idx, frame in enumerate(playfair_cuboid):
        for row_idx, row in enumerate(frame):
            if symbol_to_move in row:
                col_idx = row.index(symbol_to_move)
                return frame_idx, row_idx, col_idx
    raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cuboid.")


def _get_chars_for_coordinates(coordinate: tuple[int, int, int], rotor: list[list[list[str]]]) -> str:
    x, y, z = coordinate
    return rotor[x][y][z]


def _get_flat_index(x, y, z, size_x, size_y):
    if size_x <= 0 or size_y <= 0:
        raise ValueError("size dimensions must be greater than 0")
    return x * size_y * size_x + y * size_x + z


def _get_prefix_order_number_quartet(order_number: int) -> str:
    order_number_str = str(order_number)
    assert len(order_number_str) == 1, "Invalid order number"
    pad_symbols = ["", "", "", order_number_str]
    random.shuffle(pad_symbols)
    return "".join(pad_symbols)


def _get_random_noise_chunk(rotor: list[list[list[str]]]) -> str:
    num_blocks = len(rotor)
    lines_per_block = len(rotor[0])
    symbols_per_line = len(rotor[0][0])
    noise_quartet_symbols = [NOISE_SYMBOL]
    while len(noise_quartet_symbols) < LENGTH_OF_QUARTET:
        coordinate = (
            random.randint(0, num_blocks - 1),
            random.randint(0, lines_per_block - 1),
            random.randint(0, symbols_per_line - 1),
        )
        x, y, z = coordinate
        found_symbol = rotor[x][y][z]
        if found_symbol not in noise_quartet_symbols:
            noise_quartet_symbols.append(found_symbol)
    random.shuffle(noise_quartet_symbols)
    return "".join(noise_quartet_symbols)


def _is_valid_coord(coord: tuple[int, int, int], inner_grid: list[list[list]]) -> bool:
    inner_x, inner_y, inner_z = coord
    is_x_valid = 0 <= inner_x < len(inner_grid)
    if not is_x_valid: return False
    is_y_valid = 0 <= inner_y < len(inner_grid[0])
    if not is_y_valid: return False
    is_z_valid = 0 <= inner_z < len(inner_grid[0][0])
    return is_z_valid


def _move_letter_to_center(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the center of the playfair cuboid."""
    num_blocks = len(playfair_cuboid)
    lines_per_block = len(playfair_cuboid[0])
    symbols_per_line = len(playfair_cuboid[0][0])
    center_position = (num_blocks // 2, lines_per_block // 2, symbols_per_line // 2)
    start_position = _find_symbol(symbol_to_move, playfair_cuboid)
    updated_cuboid = _move_symbol_in_3d_grid(start_position, center_position, playfair_cuboid)
    return updated_cuboid


def _move_letter_to_front(symbol_to_move: str, playfair_cuboid: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the front of the playfair cuboid."""
    start_position = _find_symbol(symbol_to_move, playfair_cuboid)
    updated_cuboid = _move_symbol_in_3d_grid(start_position, (0, 0, 0), playfair_cuboid)
    return updated_cuboid


def _move_symbol_in_3d_grid(
    coord1: tuple[int, int, int],
    coord2: tuple[int, int, int],
    grid: list[list[list[str]]]
) -> list[list[list[str]]]:
    """
    Moves a symbol from `coord1` to `coord2` in a 3D grid and shifts intermediate elements accordingly.

    Args:
        coord1 (tuple[int, int, int]): The (x, y, z) coordinate of the symbol to move.
        coord2 (tuple[int, int, int]): The (x, y, z) coordinate where the symbol is to be moved.
        grid (list[list[list[str]]]): A 3D grid of symbols.

    Returns:
        list[list[list[str]]]: The updated grid after moving the symbol.
    """
    if not (_is_valid_coord(coord1, grid) and _is_valid_coord(coord2, grid)):
        raise ValueError("One or both coordinates are out of grid bounds.")
    size_x, size_y, size_z = len(grid), len(grid[0]), len(grid[0][0])
    flat_grid = [
        grid[x][y][z]
        for x in range(size_x)
        for y in range(size_y)
        for z in range(size_z)
    ]

    idx1 = _get_flat_index(*coord1, size_x, size_y)
    idx2 = _get_flat_index(*coord2, size_x, size_y)

    symbol_to_move = flat_grid[idx1]

    # Shift elements and insert the moved symbol
    if idx1 < idx2:
        flat_grid = flat_grid[:idx1] + flat_grid[idx1 + 1:idx2 + 1] + [symbol_to_move] + flat_grid[idx2 + 1:]
    else:
        flat_grid = flat_grid[:idx2] + [symbol_to_move] + flat_grid[idx2:idx1] + flat_grid[idx1 + 1:]

    # Rebuild the 3D grid
    updated_grid = [
        [
            flat_grid[x * size_y * size_z + y * size_z : x * size_y * size_z + (y + 1) * size_z]
            for y in range(size_y)
        ]
        for x in range(size_x)
    ]
    return updated_grid


def _pad_chunk_with_rand_pad_symbols(chunk: str) -> str:
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


def generate_rotors(
    sanitized_key_phrase: str, prepared_playfair_cuboid: list[list[list[str]]], num_rotors: int = 3
) -> list[list[list[list[str]]]]:
    """
    Generate a deterministic, key-dependent reflector for quartets.

    Args:
        sanitized_key_phrase (str): The encryption key used to seed the random generator.
        prepared_playfair_cuboid (list[list[list[str]]]): The playfair cuboid with the key phrase pulled to the front
        num_rotors (int): Number of "rotors" to use

    Returns:
        list[list[list[list[str]]]]: A list of three "rotors", where each "rotor" is a 3-dimensional cuboid representing
          a playfair cuboid. These are each unique, and each based on the key_phrase provided
    """
    if not sanitized_key_phrase or not isinstance(sanitized_key_phrase, str):
        raise ValueError("sanitized_key_phrase must be a non-empty string")
    if not num_rotors or not isinstance(num_rotors, numbers.Number):
        raise ValueError("num_rotors must be an integer great than zero.")
    if (not prepared_playfair_cuboid or not isinstance(prepared_playfair_cuboid, list)) or (not prepared_playfair_cuboid[0] or not isinstance(prepared_playfair_cuboid[0], list)) or (not prepared_playfair_cuboid[0][0] or not isinstance(prepared_playfair_cuboid[0][0], list)) or (not prepared_playfair_cuboid[0][0][0] or not isinstance(prepared_playfair_cuboid[0][0][0], str)):
        raise ValueError("prepared_playfair_cuboid must be a 3-dimensional list of non-empty strings.")
    num_rotors = int(num_rotors)
    if num_rotors > len(sanitized_key_phrase):
        raise ValueError("Cannot generate more rotors than key is long")
    # Seed the random generator with the key
    random.seed(sanitized_key_phrase)

    raw_rotors = []
    for i in range(num_rotors):
        raw_rotor = prepared_playfair_cuboid.copy()
        raw_rotors.append(raw_rotor)

    key_parts = _split_key_into_parts(sanitized_key_phrase, num_rotors=num_rotors)
    finished_rotors: list[list[list[list[str]]]] = []
    for rotor_num, key_part in enumerate(key_parts):
        cur_rotor = raw_rotors[rotor_num]
        for symbol in key_part:
            cur_rotor = _move_letter_to_center(symbol, cur_rotor)
        finished_rotors.append(cur_rotor)
    return finished_rotors


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


def pad_chunk(chunk: str, padded_chunk_length: int, chunk_order_number: int, rotor: list[list[list[str]]]) -> str:
    """
    Pad an encrypted message chunk

    Args:
        chunk (str): Encrypted message chunk to pad
        padded_chunk_length (int): Desired chunk length
        chunk_order_number (int): Which chunk is this (i.e. 1-5)?
        rotor (list[list[list[str]]]): the playfair cuboid to use for padding

    Returns:
        str: Padded chunk
    """
    padded_chunk = chunk
    while len(padded_chunk) < padded_chunk_length:
        if len(padded_chunk) % LENGTH_OF_QUARTET != 0:
            padded_chunk = _pad_chunk_with_rand_pad_symbols(padded_chunk)
        random_noise_chunk = _get_random_noise_chunk(rotor)
        padded_chunk += random_noise_chunk
    prefix_order_number_quartet = _get_prefix_order_number_quartet(chunk_order_number)
    result = prefix_order_number_quartet + padded_chunk
    return result


def parse_arguments() -> tuple[str, str, str]:
    """
    Parses runtime arguments or prompts the user for input interactively.

    Returns:
        tuple[str, str, str]: A tuple containing key_phrase, mode ('encrypt' or 'decrypt'), and the message.
    """
    parser = argparse.ArgumentParser(description="Encrypt or decrypt a message using a key phrase.")
    parser.add_argument("--key_phrase", type=str, help="The key phrase for encryption/decryption.")
    parser.add_argument("--clear_text_message", type=str, help="The plaintext message to encrypt.")
    parser.add_argument("--encrypted_message", type=str, help="The encrypted message to decrypt.")

    args = parser.parse_args()

    has_key_phrase = bool(args.key_phrase)
    has_clear_text_message = bool(args.clear_text_message)
    has_encrypted_message = bool(args.encrypted_message)
    has_message = has_clear_text_message or has_encrypted_message
    has_all_parts_from_cli = has_key_phrase and has_message
    if has_clear_text_message and has_encrypted_message:
        parser.error("Provide only one of --clear_text_message or --encrypted_message, not both.")
    if has_key_phrase and not has_message:
        parser.error("You must provide either --clear_text_message or --encrypted_message with the --key_phrase.")
    if has_clear_text_message and not has_key_phrase:
        parser.error("You must provide --key_phrase with the --clear_text_message.")
    if has_encrypted_message and not has_key_phrase:
        parser.error("You must provide --key_phrase with the --encrypted_message.")

    if not has_all_parts_from_cli:  # If only partial CLI args, then CLI error is returned above
        print("No runtime arguments provided. Switching to interactive mode.")
        mode = input("Are you encrypting or decrypting? (encrypt/decrypt/both): ").strip().lower()
        while mode not in {"encrypt", "decrypt", "both"}:
            mode = input("Invalid choice. Please enter 'encrypt', 'decrypt', or 'both': ").strip().lower()

        key_phrase = input("Enter your key phrase: ").strip()
        if mode in ("encrypt", "both"):
            message = input("Enter your plaintext message: ").strip()
        else:
            message = input("Enter your encrypted message: ").strip()

        return key_phrase, mode, message

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
    if not orig_message:
        raise ValueError("Cannot encrypt an empty message")
    sanitized_string = ""
    cur_chunk = ""
    chunk_idx = 0
    for orig_char in orig_message:
        if chunk_idx >= LENGTH_OF_QUARTET:
            sanitized_string += cur_chunk
            cur_chunk = ""
            chunk_idx = 0
        if orig_char in cur_chunk:
            cur_chunk = _pad_chunk_with_rand_pad_symbols(cur_chunk)
            sanitized_string += cur_chunk
            cur_chunk = ""
            chunk_idx = 0
        cur_chunk += orig_char
        chunk_idx += 1
    cur_chunk = _pad_chunk_with_rand_pad_symbols(cur_chunk)
    sanitized_string += cur_chunk
    return sanitized_string


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
    result = indices[0] * (num_symbols**3) + indices[1] * (num_symbols**2) + indices[2] * num_symbols + indices[3]
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


def run_quartet_through_rotors(char_quartet: str, rotors: list[list[list[list[str]]]]) -> str:
    indices_by_char = {}
    cur_quartet = char_quartet
    for rotor in rotors:
        for frame_idx, cur_frame in enumerate(rotor):
            for row_idx, cur_line in enumerate(cur_frame):
                if any(char in cur_line for char in cur_quartet):
                    if cur_quartet[0] in cur_line:
                        indices_by_char[cur_quartet[0]] = (frame_idx, row_idx, cur_line.index(cur_quartet[0]))
                    if cur_quartet[1] in cur_line:
                        indices_by_char[cur_quartet[1]] = (frame_idx, row_idx, cur_line.index(cur_quartet[1]))
                    if cur_quartet[2] in cur_line:
                        indices_by_char[cur_quartet[2]] = (frame_idx, row_idx, cur_line.index(cur_quartet[2]))
                    if cur_quartet[3] in cur_line:
                        indices_by_char[cur_quartet[3]] = (frame_idx, row_idx, cur_line.index(cur_quartet[3]))
        orig_indices = []
        for cur_char in cur_quartet:
            orig_indices.append(indices_by_char[cur_char])
        num_blocks = len(rotor)
        lines_per_block = len(rotor[0])
        symbols_per_line = len(rotor[0][0])
        encrypted_indices = _get_opposite_corners(
            orig_indices[0],
            orig_indices[1],
            orig_indices[2],
            orig_indices[3],
            num_blocks,
            lines_per_block,
            symbols_per_line,
            num_quartets_encoded
        )
        num_quartets_encoded += 1
        encrypted_char_1 = _get_chars_for_coordinates(encrypted_indices[0], rotor)
        encrypted_char_2 = _get_chars_for_coordinates(encrypted_indices[1], rotor)
        encrypted_char_3 = _get_chars_for_coordinates(encrypted_indices[2], rotor)
        encrypted_char_4 = _get_chars_for_coordinates(encrypted_indices[3], rotor)
        encrypted_quartet = "".join([encrypted_char_1, encrypted_char_2, encrypted_char_3, encrypted_char_4])
        cur_quartet = encrypted_quartet
    return cur_quartet


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


def strengthen_key(
    key_phrase: str, salt: None | bytes = None, iterations: int = 100_000, key_length: int = 32
) -> tuple[bytes, bytes]:
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
    key_phrase_bytes = key_phrase.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", key_phrase_bytes, salt, iterations, dklen=key_length)  # Derived key length
    return key, salt


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
