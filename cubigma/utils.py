""" Useful shared utilities for the cubigma project. """

from copy import deepcopy
from itertools import chain
from pathlib import Path
from typing import Any, Sequence, TypeVar
import base64
import json
import hashlib
import hmac
import math
import numbers
import os
import random

import regex

LENGTH_OF_QUARTET = 4
NOISE_SYMBOL = ""


# def deterministic_randbelow(max_value: int, key_iter: iter) -> int:
#     """
#     Generate a deterministic, cryptographically secure random number below max_value.
#     """
#     random_byte = next(key_iter, None)
#     if random_byte is None:
#         raise ValueError("Key iterator exhausted, possibly insufficient entropy in the key phrase.")
#     return int(random_byte) % max_value


def _find_symbol(symbol_to_move: str, playfair_cube: list[list[list[str]]]) -> tuple[int, int, int]:
    """Finds the frame, row, and column of the given symbol in the playfair cube."""
    for frame_idx, frame in enumerate(playfair_cube):
        for row_idx, row in enumerate(frame):
            if symbol_to_move in row:
                col_idx = row.index(symbol_to_move)
                return frame_idx, row_idx, col_idx
    raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cube.")


def _get_next_corner_choices(key_phrase: str, num_quartets_encoded: int) -> list[int]:
    """
    Generates a deterministic quartet of 4 integers (0-7) based on a key phrase and the count of encoded quartets.

    Args:
        key_phrase (str): The key phrase used to seed the generator.
        num_quartets_encoded (int): The number of quartets already encoded (used to vary output).

    Returns:
        list[int]: A list of 4 integers, each between 0-7 (inclusive).
    """
    key = key_phrase.encode("utf-8")  # Use the key phrase as the key for HMAC
    message = str(num_quartets_encoded).encode("utf-8")  # Use num_quartets_encoded as part of the message
    hmac_hash = hmac.new(key, message, hashlib.sha256).digest()  # Generate a secure hash using HMAC with SHA-256
    quartet = [(byte % 8) for byte in hmac_hash[:4]]  # Extract 4 deterministic integers (0-7) from the hash
    return quartet


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
    if not is_x_valid:
        return False
    is_y_valid = 0 <= inner_y < len(inner_grid[0])
    if not is_y_valid:
        return False
    is_z_valid = 0 <= inner_z < len(inner_grid[0][0])
    return is_z_valid


def _move_letter_to_center(symbol_to_move: str, playfair_cube: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the center of the playfair cube."""
    num_blocks = len(playfair_cube)
    lines_per_block = len(playfair_cube[0])
    symbols_per_line = len(playfair_cube[0][0])
    center_position = (num_blocks // 2, lines_per_block // 2, symbols_per_line // 2)
    start_position = _find_symbol(symbol_to_move, playfair_cube)
    updated_cube = _move_symbol_in_3d_grid(start_position, center_position, playfair_cube)
    return updated_cube


def _move_letter_to_front(symbol_to_move: str, playfair_cube: list[list[list[str]]]) -> list[list[list[str]]]:
    """Moves the symbol to the front of the playfair cube."""
    start_position = _find_symbol(symbol_to_move, playfair_cube)
    updated_cube = _move_symbol_in_3d_grid(start_position, (0, 0, 0), playfair_cube)
    return updated_cube


def _move_symbol_in_3d_grid(
    coord1: tuple[int, int, int], coord2: tuple[int, int, int], grid: list[list[list[str]]]
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
    flat_grid = [grid[x][y][z] for x in range(size_x) for y in range(size_y) for z in range(size_z)]

    idx1 = _get_flat_index(*coord1, size_x, size_y)
    idx2 = _get_flat_index(*coord2, size_x, size_y)

    symbol_to_move = flat_grid[idx1]

    # Shift elements and insert the moved symbol
    idx_start = idx1 + 1
    if idx1 < idx2:
        idx_end = idx2 + 1
        flat_grid = flat_grid[:idx1] + flat_grid[idx_start:idx_end] + [symbol_to_move] + flat_grid[idx_end:]
    else:
        flat_grid = flat_grid[:idx2] + [symbol_to_move] + flat_grid[idx2:idx1] + flat_grid[idx_start:]

    # Rebuild the 3D grid
    updated_grid = []
    for x in range(size_x):
        cur_elements = []
        for y in range(size_y):
            idx_start = x * size_y * size_z + y * size_z
            idx_end = x * size_y * size_z + (y + 1) * size_z
            cur_element = flat_grid[idx_start:idx_end]
            cur_elements.append(cur_element)
        updated_grid.append(cur_elements)
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


def _read_and_validate_config(mode: str = "") -> tuple[int, int, list[int], str, bool]:
    config = read_config()
    cube_length = config.get("LENGTH_OF_CUBE", None)
    if cube_length is None:
        raise ValueError("LENGTH_OF_CUBE not found in config.json")
    if not isinstance(cube_length, int):
        raise ValueError("LENGTH_OF_CUBE (in config.json) must have an integer value")
    if cube_length < 5 or cube_length > 11:
        raise ValueError("LENGTH_OF_CUBE (in config.json) must be greater than 4 and lower than 12")

    num_rotors_to_make = config.get("NUMBER_OF_ROTORS_TO_GENERATE", None)
    if num_rotors_to_make is None:
        raise ValueError("NUMBER_OF_ROTORS_TO_GENERATE not found in config.json")
    if not isinstance(num_rotors_to_make, int):
        raise ValueError("NUMBER_OF_ROTORS_TO_GENERATE (in config.json) must have an integer value")
    if num_rotors_to_make < 1:
        raise ValueError("NUMBER_OF_ROTORS_TO_GENERATE (in config.json) must be greater than 0")

    rotors_to_use = config.get("ROTORS_TO_USE", None)
    if rotors_to_use is None:
        raise ValueError("ROTORS_TO_USE not found in config.json")
    if not isinstance(rotors_to_use, list):
        raise ValueError("ROTORS_TO_USE (in config.json) must be a list of integers")
    seen_rotor_values: list[int] = []
    for index, rotor_item in enumerate(rotors_to_use):
        if not isinstance(rotor_item, int):
            raise ValueError(f"ROTORS_TO_USE (in config.json) contains a non-integer value at index: {index}")
        if rotor_item < 0 or rotor_item >= num_rotors_to_make:
            first_half = "ROTORS_TO_USE (in config.json) all rotor"
            raise ValueError(f"{first_half} values must be between 0 & the number of rotors generated")
        if rotor_item in seen_rotor_values:
            raise ValueError("ROTORS_TO_USE (in config.json) all rotor values must be unique")
        seen_rotor_values.append(rotor_item)

    if not mode:
        mode = config.get("ENCRYPT_OR_DECRYPT", None)
        if mode is None:
            raise ValueError("ENCRYPT_OR_DECRYPT not found in config.json")
    if not isinstance(mode, str):
        raise ValueError("ENCRYPT_OR_DECRYPT (in config.json) must be a string")
    if mode.upper() not in ["ENCRYPT", "DECRYPT"]:
        raise ValueError("ENCRYPT_OR_DECRYPT (in config.json) must be either 'ENCRYPT' or 'DECRYPT'")

    should_use_steganography = config.get("ALSO_USE_STEGANOGRAPHY", None)
    if should_use_steganography is None:
        raise ValueError("ALSO_USE_STEGANOGRAPHY not found in config.json")
    if not isinstance(should_use_steganography, bool):
        raise ValueError("ALSO_USE_STEGANOGRAPHY (in config.json) must be a boolean value (e.g. true or false)")

    return cube_length, num_rotors_to_make, rotors_to_use, mode, should_use_steganography


def _rotate_2d_array(arr: list[list[str]], direction: int) -> list[list[str]]:
    """
    Rotate a 2D array clockwise or counterclockwise.

    Args:
        arr: The 2D array to rotate.
        direction: 1 for clockwise, -1 for counterclockwise.

    Returns:
        A new 2D array rotated in the specified direction.
    """
    if direction == 1:  # Clockwise
        return [list(row) for row in zip(*arr[::-1])]
    elif direction == -1:  # Counterclockwise
        return [list(row) for row in zip(*arr)][::-1]
    raise ValueError("Direction must be 1 (clockwise) or -1 (counterclockwise).")


T = TypeVar("T")  # Generic type variable for elements in the sequence


def _secure_shuffle(sequence: Sequence[T], sanitized_key_phrase: str) -> list[T]:
    """
    Shuffle a sequence using secrets for cryptographic security.

    Args:
        sequence (Sequence[T]): The input sequence to shuffle.
        sanitized_key_phrase (str): A sanitized key phrase for deterministic shuffling.

    Returns:
        list[T]: A securely shuffled list containing the elements of the input sequence.
    """
    # # Hash the key phrase to create a deterministic seed
    # key_hash = hashlib.sha256(sanitized_key_phrase.encode()).digest()
    #
    # # Create an iterator over the bytes of the hashed key, cycling if necessary
    # hash_iter = iter(key_hash * ((len(sequence) // len(key_hash)) + 1))  # Repeat hash bytes as needed
    #
    # # Shuffle the sequence using deterministic randomness
    # shuffled = list(sequence)
    # for i in range(len(shuffled) - 1, 0, -1):
    #     j = deterministic_randbelow(i + 1, hash_iter)
    #     shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    # return shuffled

    # Derive a deterministic seed from the sanitized_key_phrase
    seed = int(hashlib.sha256(sanitized_key_phrase.encode()).hexdigest(), 16)

    # Initialize a random generator with the deterministic seed
    rng = random.Random(seed)

    shuffled = list(sequence)
    for i in range(len(shuffled) - 1, 0, -1):
        j = rng.randint(0, i)  # Generate a random index deterministically
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def _shuffle_cube_with_key_phrase(
    sanitized_key_phrase: str, orig_cube: list[list[list[str]]], value_unique_to_each_rotor: str
) -> list[list[list[str]]]:
    """
    Shuffles the elements of a 3-dimensional list in-place for cryptographic use.

    Args:
        sanitized_key_phrase (str): strengthened, sanitized key
        orig_cube (list[list[list[str]]]): A 3-dimensional list of strings to shuffle.
        value_unique_to_each_rotor (str): string representation of a number that changes for each rotor

    Returns:
        list[list[list[str]]]: The shuffled 3-dimensional list.
    """
    # Flatten the entire cube into a single list of elements
    flat_cube = list(chain.from_iterable(chain.from_iterable(orig_cube)))

    shuffled_flat = _secure_shuffle(flat_cube, f"{sanitized_key_phrase}|{value_unique_to_each_rotor}")

    # Reshape the flattened list back into the original cube structure
    # cube_shape = [[[len(inner) for inner in outer] for outer in orig_cube]]
    reshaped_cube = deepcopy(orig_cube)
    flat_iter = iter(shuffled_flat)
    for outer in reshaped_cube:
        for inner in outer:
            for i in range(len(inner)):
                inner[i] = next(flat_iter)
    return reshaped_cube


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


def generate_rotors(
    sanitized_key_phrase: str,
    raw_cube: list[list[list[str]]],
    num_rotors_to_make: int | None = None,
    rotors_to_use: list[int] | None = None,
    orig_key_length: int | None = None,
) -> list[list[list[list[str]]]]:
    """
    Generate a deterministic, key-dependent reflector for quartets.

    Args:
        sanitized_key_phrase (str): The encryption key (strengthened & sanitized) used to seed the random generator.
        raw_cube (list[list[list[str]]]): The playfair cube with the key phrase pulled to the front
        num_rotors_to_make (int): Number of "rotors" to generate
        rotors_to_use (list[int]): Indices of which "rotors" to actually use
        orig_key_length (int | None): How long the key was before it was strengthened to 44 chars long

    Returns:
        list[list[list[list[str]]]]: A list of "rotors", where each "rotor" is a 3-dimensional cube representing a
          playfair cube. These have been shuffled (based on the key_phrase provided)
    """
    if not sanitized_key_phrase or not isinstance(sanitized_key_phrase, str):
        raise ValueError("sanitized_key_phrase must be a non-empty string")
    if (
        (not raw_cube or not isinstance(raw_cube, list))
        or (not raw_cube[0] or not isinstance(raw_cube[0], list))
        or (not raw_cube[0][0] or not isinstance(raw_cube[0][0], list))
        or (not raw_cube[0][0][0] or not isinstance(raw_cube[0][0][0], str))
    ):
        raise ValueError("raw_cube must be a 3-dimensional list of non-empty strings.")
    if not num_rotors_to_make or not isinstance(num_rotors_to_make, numbers.Number) or num_rotors_to_make < 1:
        raise ValueError("num_rotors must be an integer great than zero.")
    if not rotors_to_use or not isinstance(rotors_to_use, list):
        raise ValueError("NUMBER_OF_ROTORS_TO_GENERATE (in config.json) must be a non-empty list of integers")
    if not orig_key_length or not isinstance(orig_key_length, int):
        raise ValueError("orig_key_length must be a integer greater than 0")
    seen_rotor_values: list[int] = []
    for rotor_item in rotors_to_use:
        if (
            not isinstance(rotor_item, int)
            or rotor_item < 0
            or rotor_item >= num_rotors_to_make
            or rotor_item in seen_rotor_values
        ):
            first_half = "NUMBER_OF_ROTORS_TO_GENERATE (in config.json) all rotor values must be"
            raise ValueError(f"{first_half} unique integers between 0 & the number of rotors generated")
        seen_rotor_values.append(rotor_item)

    random.seed(sanitized_key_phrase)  # Seed the random generator with the key

    generated_rotors = []
    random_prime_1 = 7
    random_prime_2 = 13
    for generated_rotor_idx in range(num_rotors_to_make):
        raw_rotor = deepcopy(raw_cube)
        base = (generated_rotor_idx + random_prime_1) * random_prime_2
        exponent = orig_key_length + generated_rotor_idx
        value_unique_to_each_rotor = str(math.pow(base, exponent))
        shuffled_rotor = _shuffle_cube_with_key_phrase(sanitized_key_phrase, raw_rotor, value_unique_to_each_rotor)
        generated_rotors.append(shuffled_rotor)

    rotors_ready_for_use: list[list[list[list[str]]]] = []
    for desired_rotor_index in rotors_to_use:
        rotors_ready_for_use.append(generated_rotors[desired_rotor_index])
    return rotors_ready_for_use


def get_chars_for_coordinates(coordinate: tuple[int, int, int], rotor: list[list[list[str]]]) -> str:
    x, y, z = coordinate
    return rotor[x][y][z]


def get_opposite_corners(
    point_1: tuple[int, int, int],
    point_2: tuple[int, int, int],
    point_3: tuple[int, int, int],
    point_4: tuple[int, int, int],
    num_blocks: int,
    lines_per_block: int,
    symbols_per_line: int,
    key_phrase: str,
    num_quartets_encoded: int,
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """
    Given four corners of a rectangular cube, find the other four corners.

    Args:
        point_1: A tuple representing the first point (x, y, z).
        point_2: A tuple representing the second point (x, y, z).
        point_3: A tuple representing the third point (x, y, z).
        point_4: A tuple representing the fourth point (x, y, z).
        num_blocks (int): How tall in the cube (x).
        lines_per_block (int): How long in the cube (y).
        symbols_per_line (int): How wide in the cube (z).
        key_phrase (str): Secret key phrase
        num_quartets_encoded (int): Number of quartet encodings performed thus far

    Returns:
        A tuple of four tuples, each representing the coordinates of the remaining corners.
    """
    # Check for unique points
    given_points = {point_1, point_2, point_3, point_4}
    if len(given_points) != LENGTH_OF_QUARTET:
        raise ValueError("The provided points must be unique and represent adjacent corners of a rectangular cube.")

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
    all_points = [point_1, point_2, point_3, point_4, point_5, point_6, point_7, point_8]

    indices_to_choose = _get_next_corner_choices(key_phrase, num_quartets_encoded)
    chosen_point_1 = all_points[indices_to_choose[0]]
    chosen_point_2 = all_points[indices_to_choose[1]]
    chosen_point_3 = all_points[indices_to_choose[2]]
    chosen_point_4 = all_points[indices_to_choose[3]]
    return chosen_point_1, chosen_point_2, chosen_point_3, chosen_point_4


def pad_chunk(chunk: str, padded_chunk_length: int, chunk_order_number: int, rotor: list[list[list[str]]]) -> str:
    """
    Pad an encrypted message chunk

    Args:
        chunk (str): Encrypted message chunk to pad
        padded_chunk_length (int): Desired chunk length
        chunk_order_number (int): Which chunk is this (i.e. 1-5)?
        rotor (list[list[list[str]]]): the playfair cube to use for padding

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


def parse_arguments(
    key_phrase: str = "", mode: str = "", message: str = ""
) -> tuple[str, str, str, int, int, list[int], bool]:
    """
    Parses config and prompts the user for input interactively.

    Returns:
        tuple[str, str, str, int, int, list[int], bool]: A tuple containing:
          * key_phrase
          * mode ('encrypt' or 'decrypt')
          * the message
          * length of playfair cube
          * number of rotors to generate
          * which rotors to use
          * whether to use steganography in addition to encryption
    """

    cube_length, num_rotors_to_make, rotors_to_use, mode, should_use_steganography = _read_and_validate_config(
        mode=mode
    )

    if not key_phrase:
        key_phrase = input("Enter your key phrase: ").strip()
    if not message:
        if mode.lower() == "encrypt":
            message = input("Enter your plaintext message: ").strip()
        elif mode.lower() == "decrypt":
            message = input("Enter your encrypted message: ").strip()
        else:
            raise ValueError("Unknown mode")

    return key_phrase, mode.lower(), message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography


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


def rotate_slice_of_cube(cube: list[list[list[str]]], combined_seed: str) -> list[list[list[str]]]:
    """
    Rotate a slice of a 3D cube (3-dimensional array of chars) along a chosen axis.

    Args:
        cube: A 3D list representing the cube.
        combined_seed: A seed string to ensure deterministic random behavior.

    Returns:
        A new 3D list with the specified slice rotated.
    """
    random.seed(combined_seed)  # Ensure this logic is deterministic
    axis = random.choice(["X", "Y", "Z"])
    rotate_dir = random.choice([-1, 1])  # -1: counterclockwise, 1: clockwise
    slice_idx_to_rotate = random.randint(0, len(cube) - 1)

    new_cube = deepcopy(cube)  # Create a copy of the cube to avoid mutating the input

    if axis == "X":
        # Rotate along the X-axis: affecting cube[slice_idx_to_rotate][i][j]
        slice_to_rotate = [row[:] for row in cube[slice_idx_to_rotate]]
        rotated_slice = _rotate_2d_array(slice_to_rotate, rotate_dir)
        new_cube[slice_idx_to_rotate] = rotated_slice
    elif axis == "Y":
        # Rotate along the Y-axis: affecting cube[i][slice_idx_to_rotate][j]
        slice_to_rotate = [frame[slice_idx_to_rotate] for frame in cube]
        rotated_slice = _rotate_2d_array(slice_to_rotate, rotate_dir)
        for idx, layer in enumerate(rotated_slice):
            new_cube[idx][slice_idx_to_rotate] = layer
    elif axis == "Z":
        # Rotate along the Z-axis: affecting cube[i][j][slice_idx_to_rotate]
        slice_to_rotate = []
        for frame_idx, frame in enumerate(cube):
            row_to_rotate = []
            for row_idx, row in enumerate(frame):
                row_to_rotate.append(row[slice_idx_to_rotate])
            slice_to_rotate.append(row_to_rotate)
        rotated_slice = _rotate_2d_array(slice_to_rotate, rotate_dir)
        for frame_idx, frame in enumerate(cube):
            for row_idx, row in enumerate(frame):
                max_idx = len(row) - 1
                rotated_frame_col_idx = max_idx - row_idx
                new_cube[frame_idx][row_idx][slice_idx_to_rotate] = rotated_slice[frame_idx][rotated_frame_col_idx]
    return new_cube


def run_quartet_through_reflector(char_quartet: str, strengthened_key_phrase: str, num_of_encoded_quartets: int) -> str:
    """
    Reflects the quartet deterministically using a hash-based reordering.

    Args:
        char_quartet (str): The input quartet of symbols.
        strengthened_key_phrase (str): A strengthened key phrase
        num_of_encoded_quartets (int): This changes with each encoding, so that the same quartet gets encoded
          differently each time

    Returns:
        str: The reflected quartet.
    """

    # Hash the quartet to determine the reordering
    hash_input = f"{char_quartet}|{strengthened_key_phrase}|{num_of_encoded_quartets}"
    quartet_hash = hashlib.sha256(hash_input.encode()).digest()

    # Determine the reordering using the first 4 bytes of the hash
    order = sorted(range(4), key=lambda i: quartet_hash[i])

    # Reorder the quartet based on the computed order
    return "".join(char_quartet[i] for i in order)


def sanitize(raw_input: str) -> str:
    if raw_input.startswith("\\"):
        return raw_input.strip().replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return raw_input.replace("\n", "")


def split_to_human_readable_symbols(s: str, expected_number_of_graphemes: int | None = LENGTH_OF_QUARTET) -> list[str]:
    """
    Splits a string with a user-perceived length of 4 into its 4 human-discernible symbols.

    Args:
        s (str): The input string, guaranteed to have a user_perceived_length of 4.
        expected_number_of_graphemes (int): Optional. The number of graphemes to enforce

    Returns:
        list[str]: A list of 4 human-readable symbols, each as a separate string.
    """
    # Match grapheme clusters (human-discernible symbols)
    graphemes = regex.findall(r"\X", s)
    # Ensure the string has exactly 4 human-discernible symbols
    if expected_number_of_graphemes:
        if len(graphemes) != expected_number_of_graphemes:
            raise ValueError("The input string must have a user-perceived length of 4.")
    return graphemes


def strengthen_key(
    key_phrase: str, salt: None | bytes = None, iterations: int = 200_000, key_length: int = 32
) -> tuple[str, str]:
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
    if salt is None:
        salt = os.urandom(16)  # Use a secure random salt if not provided
    key_phrase_bytes = key_phrase.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", key_phrase_bytes, salt, iterations, dklen=key_length)  # Derived key length
    b64_key = base64.b64encode(key).decode("utf-8")  # always 44 chars long
    b64_salt = base64.b64encode(salt).decode("utf-8")  # always 24 chars long
    # if len(b64_key) != 44 or len(b64_salt) != 24:
    #     print(f"This should not happen! {len(b64_key)} != 44 or {len(b64_salt)} != 24")
    return b64_key, b64_salt


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
