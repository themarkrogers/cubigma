""" Useful shared utilities for the cubigma project. """

from copy import deepcopy
from itertools import chain
import math
from numbers import Number
from pathlib import Path
from typing import Any
import json

import regex

from cubigma.core import (
    # from core import (
    get_independently_deterministic_random_rotor_info,
    get_non_deterministically_random_int,
    get_non_deterministically_random_shuffled,
    random_int_for_input,
    shuffle_for_input,
    DeterministicRandomCore,
)

LENGTH_OF_TRIO = 3
NOISE_SYMBOL = ""


def _find_symbol(symbol_to_move: str, playfair_cube: list[list[list[str]]]) -> tuple[int, int, int]:
    """Finds the frame, row, and column of the given symbol in the playfair cube."""
    for frame_idx, frame in enumerate(playfair_cube):
        for row_idx, row in enumerate(frame):
            if symbol_to_move in row:
                col_idx = row.index(symbol_to_move)
                return frame_idx, row_idx, col_idx
    raise ValueError(f"Symbol '{symbol_to_move}' not found in playfair_cube.")


def _get_flat_index(x, y, z, size_x, size_y):
    if size_x <= 0 or size_y <= 0:
        raise ValueError("size dimensions must be greater than 0")
    return x * size_y * size_x + y * size_x + z


def _get_prefix_order_number_trio(order_number: int) -> str:
    order_number_str = str(order_number)
    assert len(order_number_str) == 1, "Invalid order number"
    # pad_symbols = ["", "", "", order_number_str]
    pad_symbols = ["", "", order_number_str]
    shuffled_pad_symbols = get_non_deterministically_random_shuffled(pad_symbols)
    return "".join(shuffled_pad_symbols)


def _get_random_noise_chunk(rotor: list[list[list[str]]]) -> str:
    num_blocks = len(rotor)
    lines_per_block = len(rotor[0])
    symbols_per_line = len(rotor[0][0])
    noise_trio_symbols = [NOISE_SYMBOL]
    while len(noise_trio_symbols) < LENGTH_OF_TRIO:
        coordinate = (
            get_non_deterministically_random_int(0, num_blocks - 1),
            get_non_deterministically_random_int(0, lines_per_block - 1),
            get_non_deterministically_random_int(0, symbols_per_line - 1),
        )
        x, y, z = coordinate
        found_symbol = rotor[x][y][z]
        if found_symbol not in noise_trio_symbols:
            noise_trio_symbols.append(found_symbol)
    shuffled_trio_symbols = get_non_deterministically_random_shuffled(noise_trio_symbols)
    return "".join(shuffled_trio_symbols)


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


def _pad_chunk_with_rand_pad_symbols(chunk: str) -> str:
    if len(chunk) < 1:
        raise ValueError("Chunk cannot be empty")
    pad_symbols = ["", "", ""]
    max_pad_idx = len(pad_symbols) - 1
    while len(chunk) < LENGTH_OF_TRIO:
        new_random_number = get_non_deterministically_random_int(0, max_pad_idx)
        random_pad_symbol = pad_symbols[new_random_number]
        if random_pad_symbol not in chunk:
            chunk += random_pad_symbol
    return chunk


def _read_and_validate_config(mode: str = "") -> tuple[int, int, list[int], str, bool, list[str]]:
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

    plugboard_values = config.get("PLUGBOARD", None)
    if plugboard_values is None:
        raise ValueError("PLUGBOARD not found in config.json")
    if not isinstance(plugboard_values, list):
        raise ValueError("PLUGBOARD (in config.json) must be a list of symbol pairs")

    seen_plugboard_symbols: list[str] = []
    for index, raw_plugboard_val in enumerate(plugboard_values):
        if not isinstance(raw_plugboard_val, str):
            raise ValueError(f"PLUGBOARD (in config.json) contains a non-string value at index: {index}")
        if _user_perceived_length(raw_plugboard_val) != 2:
            first_half = "PLUGBOARD (in config.json) all plugboard values must be pairs of symbols."
            raise ValueError(f"{first_half} index {index} has length of {_user_perceived_length(raw_plugboard_val)}")
        for plugboard_symbol in split_to_human_readable_symbols(raw_plugboard_val, expected_number_of_graphemes=2):
            if plugboard_symbol in seen_plugboard_symbols:
                first_half = "PLUGBOARD (in config.json) all plugboard symbols must be unique."
                raise ValueError(f"{first_half} {plugboard_symbol} appears more than once")
            seen_plugboard_symbols.append(plugboard_symbol)

    return cube_length, num_rotors_to_make, rotors_to_use, mode, should_use_steganography, plugboard_values


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
    if direction == -1:  # Counterclockwise
        return [list(row) for row in zip(*arr)][::-1]
    raise ValueError("Direction must be 1 (clockwise) or -1 (counterclockwise).")


def _shuffle_cube_with_key_phrase(
    strengthened_key_phrase: str,
    orig_cube: list[list[list[str]]],
    value_unique_to_each_rotor: str,
) -> list[list[list[str]]]:
    """
    Shuffles the elements of a 3-dimensional list in-place for cryptographic use.

    Args:
        strengthened_key_phrase (str): strengthened, sanitized key
        orig_cube (list[list[list[str]]]): A 3-dimensional list of strings to shuffle.
        value_unique_to_each_rotor (str): string representation of a number that changes for each rotor

    Returns:
        list[list[list[str]]]: The shuffled 3-dimensional list.
    """
    # Flatten the entire cube into a single list of elements
    flat_cube = list(chain.from_iterable(chain.from_iterable(orig_cube)))

    shuffled_flat = shuffle_for_input(f"{strengthened_key_phrase}|{value_unique_to_each_rotor}", flat_cube)

    # Reshape the flattened list back into the original cube structure
    reshaped_cube = deepcopy(orig_cube)
    flat_iter = iter(shuffled_flat)
    for outer in reshaped_cube:
        for inner in outer:
            for i in range(len(inner)):
                inner[i] = next(flat_iter)
    return reshaped_cube


def generate_cube_from_symbols(
    symbols: list[str], num_blocks: int = -1, lines_per_block: int = -1, symbols_per_line: int = -1
) -> list[list[list[str]]]:
    symbols_per_block = symbols_per_line * lines_per_block
    cube = []
    for block in range(num_blocks):
        new_frame = []
        for row in range(lines_per_block):
            start_idx = block * symbols_per_block + row * symbols_per_line
            end_idx = block * symbols_per_block + (row + 1) * symbols_per_line
            raw_symbols = symbols[start_idx:end_idx]
            if _user_perceived_length("".join(raw_symbols)) != symbols_per_line:
                raise ValueError("Something has failed")
            new_row = [i.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\") for i in raw_symbols]
            # new_row = []
            # for i in raw_symbols:
            #     foo = i.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
            #     new_row.append(foo)
            assert len(new_row) == symbols_per_line, "Something else has failed."
            new_frame.append(new_row)
        cube.append(new_frame)
    return cube


def generate_plugboard(plugboard_values: list[str]) -> dict[str, str]:
    """
    Generate a "plugboard" that swaps symbols before and after encryption

    Args:
        plugboard_values (list[str]): a list of symbol pairs

    Returns:
        a dictionary of one symbol to another
    """
    plugboard = {}
    seen_plugboard_symbols = []
    for index, symbol_pair in enumerate(plugboard_values):
        symbols = split_to_human_readable_symbols(symbol_pair, expected_number_of_graphemes=None)
        if len(symbols) != 2:
            first_half = "Plugboard values are expected to all be pairs of symbols."
            raise ValueError(f"{first_half} Something else is the case at index {index}")
        symbol_1 = symbols[0]
        symbol_2 = symbols[1]
        if symbol_1 in seen_plugboard_symbols or symbol_2 in seen_plugboard_symbols:
            raise ValueError("Cannot create a plugboard with duplicate symbols")
        seen_plugboard_symbols += [symbol_1, symbol_2]
        plugboard[symbol_1] = symbol_2
        plugboard[symbol_2] = symbol_1
    return plugboard


def generate_reflector(symbols: list[str], random_core: DeterministicRandomCore) -> dict[str, str]:
    """
    Generate a "reflector" that swaps symbols in the middle of encryption

    Args:
        symbols (list[str]): a list of all possible symbols
        random_core (DeterministicRandomCore): The random_core from the cubigma instance calling this

    Returns:
        a dictionary of one symbol to another
    """
    # Create a list of all possible symbols
    new_symbols = random_core.shuffle(symbols.copy())

    # Create pairs and map them bidirectionally
    reflector = {}
    num_symbols = len(new_symbols)
    last_index = num_symbols - 1
    middle_index = int(num_symbols / 2.0)
    is_length_odd = middle_index != num_symbols / 2.0
    if num_symbols == 1:
        only_symbol = symbols[0]
        reflector[only_symbol] = only_symbol
        return reflector
    for i in range(0, middle_index):
        if i == 0 and is_length_odd:
            q1, q2 = new_symbols[i], new_symbols[last_index - i]
            q3 = new_symbols[middle_index]
            reflector[q1] = q2
            reflector[q2] = q3
            reflector[q3] = q1
        else:
            q1, q2 = new_symbols[i], new_symbols[last_index - i]
            reflector[q1] = q2
            reflector[q2] = q1
    return reflector


def generate_rotors(
    strengthened_key_phrase: str,
    raw_cube: list[list[list[str]]],
    num_rotors_to_make: int | None = None,
    rotors_to_use: list[int] | None = None,
    orig_key_length: int | None = None,
) -> list[list[list[list[str]]]]:
    """
    Generate a deterministic, key-dependent reflector for trios.

    Args:
        strengthened_key_phrase (str): The encryption key (strengthened & sanitized) used to seed the random generator.
        raw_cube (list[list[list[str]]]): The playfair cube with the key phrase pulled to the front
        num_rotors_to_make (int): Number of "rotors" to generate
        rotors_to_use (list[int]): Indices of which "rotors" to actually use
        orig_key_length (int | None): How long the key was before it was strengthened to 44 chars long

    Returns:
        list[list[list[list[str]]]]: A list of "rotors", where each "rotor" is a 3-dimensional cube representing a
          playfair cube. These have been shuffled (based on the key_phrase provided)
    """
    if not strengthened_key_phrase or not isinstance(strengthened_key_phrase, str):
        raise ValueError("sanitized_key_phrase must be a non-empty string")
    if (
        (not raw_cube or not isinstance(raw_cube, list))
        or (not raw_cube[0] or not isinstance(raw_cube[0], list))
        or (not raw_cube[0][0] or not isinstance(raw_cube[0][0], list))
        or (not raw_cube[0][0][0] or not isinstance(raw_cube[0][0][0], str))
    ):
        raise ValueError("raw_cube must be a 3-dimensional list of non-empty strings.")
    if not num_rotors_to_make or not isinstance(num_rotors_to_make, Number) or num_rotors_to_make < 1:
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

    generated_rotors = []
    arbitrary_prime_1 = 7
    arbitrary_prime_2 = 13
    for generated_rotor_idx in range(num_rotors_to_make):
        raw_rotor = deepcopy(raw_cube)
        base = (generated_rotor_idx + arbitrary_prime_1) * arbitrary_prime_2
        exponent = orig_key_length + generated_rotor_idx
        value_unique_to_each_rotor = str(math.pow(base, exponent))

        are_all_pad_symbols_in_same_frame = True
        while are_all_pad_symbols_in_same_frame:
            shuffled_rotor = _shuffle_cube_with_key_phrase(
                strengthened_key_phrase, raw_rotor, value_unique_to_each_rotor
            )
            # ToDo: We need to ensure that all three pad symbols are NOT on the same x, y, or z as each other
            are_all_pad_symbols_in_same_frame = False  # ToDo: Implement this
        generated_rotors.append(shuffled_rotor)

    rotors_ready_for_use: list[list[list[list[str]]]] = []
    for desired_rotor_index in rotors_to_use:
        rotors_ready_for_use.append(generated_rotors[desired_rotor_index])
    return rotors_ready_for_use


def get_symbol_for_coordinates(coordinate: tuple[int, int, int], rotor: list[list[list[str]]]) -> str:
    x, y, z = coordinate
    return rotor[x][y][z]


def _transpose_coordinates(
    coordinates: list[tuple[int, int, int]], cube_length: int, is_encrypting: bool, key_phrase: str
) -> list[tuple[int, int, int]]:
    # ToDo: Derive these values from the key (instead of hardcoding them)
    x_mod = random_int_for_input(f"{key_phrase}|x", -2, 2)
    y_mod = random_int_for_input(f"{key_phrase}|y", -2, 2)
    z_mod = random_int_for_input(f"{key_phrase}|z", -2, 2)

    max_index = cube_length - 1
    new_coordinates = []
    for coordinate in coordinates:
        x, y, z = coordinate

        if is_encrypting:
            new_x = x + x_mod
        else:
            new_x = x - x_mod
        if new_x > max_index:
            new_x -= cube_length
        if new_x < 0:
            new_x = cube_length + new_x

        if is_encrypting:
            new_y = y + y_mod
        else:
            new_y = y - y_mod
        if new_y > max_index:
            new_y -= cube_length
        if new_y < 0:
            new_y = cube_length + new_y

        if is_encrypting:
            new_z = z + z_mod
        else:
            new_z = z - z_mod
        if new_z > max_index:
            new_z -= cube_length
        if new_z < 0:
            new_z = cube_length + new_z

        new_coordinate = new_x, new_y, new_z
        new_coordinates.append(new_coordinate)
    return new_coordinates


def _cyclically_permute_coordinates(
    coordinates: list[tuple[int, int, int]], cube_length: int, is_encrypting: bool, key_phrase: str
) -> list[tuple[int, int, int]]:
    max_index = cube_length - 1
    new_coordinates = []
    for idx, coordinate in enumerate(coordinates):
        x, y, z = coordinate
        if idx == 0:
            next_idx = idx + 1
            prev_idx = max_index
        elif idx == max_index:
            next_idx = 0
            prev_idx = idx - 1
        else:
            next_idx = idx + 1
            prev_idx = idx - 1
        next_coordinate = coordinates[next_idx]
        prev_coordinate = coordinates[prev_idx]
        x_n, y_n, z_n = next_coordinate
        x_p, y_p, z_p = prev_coordinate
        if is_encrypting:
            new_coordinate = x, y_n, z_p
        else:
            new_coordinate = x, y_p, z_n
        new_coordinates.append(new_coordinate)
    return new_coordinates


def _invert_coordinates(
    coordinates: list[tuple[int, int, int]], cube_length: int, is_encrypting: bool, key_phrase: str
) -> list[tuple[int, int, int]]:
    max_index = cube_length - 1
    reflection_index = random_int_for_input(key_phrase, 0, max_index)
    new_coordinates = []
    for coordinate in coordinates:
        x, y, z = coordinate
        new_coordinate = reflection_index - x, reflection_index - y, reflection_index - z
        new_coordinates.append(new_coordinate)
    return new_coordinates


def get_encrypted_coordinates(
    point_1: tuple[int, int, int],
    point_2: tuple[int, int, int],
    point_3: tuple[int, int, int],
    cube_length: int,
    key_phrase: str,
    num_trios_encoded: int,
    is_encrypting: bool,
) -> list[tuple[int, int, int]]:
    """
    Given four corners of a rectangular cube, find the other four corners.

    Args:
        point_1: A tuple representing the first point (x, y, z).
        point_2: A tuple representing the second point (x, y, z).
        point_3: A tuple representing the third point (x, y, z).
        cube_length (int): How many symbols are in each dimension of the cube
        key_phrase (str): Secret key phrase
        num_trios_encoded (int): Number of trio encodings performed thus far
        is_encrypting (bool): encrypting or decrypting

    Returns:
        A tuple of three tuples, each representing the coordinates of the encrypted symbols.
    """
    # ToDo: Confirm the tests on this function are complete
    combined_key = f"{key_phrase}|{num_trios_encoded}"
    operations = [_cyclically_permute_coordinates, _invert_coordinates, _transpose_coordinates]
    shuffled_ops = shuffle_for_input(combined_key, operations)
    cur_points = [point_1, point_2, point_3]
    for coordinate_operation in shuffled_ops:
        cur_points = coordinate_operation(cur_points, cube_length, is_encrypting, combined_key)
    return cur_points


def pad_chunk(chunk: str, padded_chunk_length: int, chunk_order_number: int, rotor: list[list[list[str]]]) -> str:
    """
    Pad an encrypted message chunk
ter
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
        if len(padded_chunk) % LENGTH_OF_TRIO != 0:
            padded_chunk = _pad_chunk_with_rand_pad_symbols(padded_chunk)
        random_noise_chunk = _get_random_noise_chunk(rotor)
        padded_chunk += random_noise_chunk
    prefix_order_number_trio = _get_prefix_order_number_trio(chunk_order_number)
    result = prefix_order_number_trio + padded_chunk
    return result


def parse_arguments(
    key_phrase: str = "", mode: str = "", message: str = ""
) -> tuple[str, str, str, int, int, list[int], bool, list[str]]:
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
          * a list of pairs of symbols to use as the plugboard
    """

    tuple_result = _read_and_validate_config(mode=mode)
    cube_length, num_rotors_to_make, rotors_to_use, mode, should_use_steganography, plugboard_values = tuple_result

    if not key_phrase:
        key_phrase = input("Enter your key phrase: ").strip()
    if not message:
        if mode.lower() == "encrypt":
            message = input("Enter your plaintext message: ").strip()
        elif mode.lower() == "decrypt":
            message = input("Enter your encrypted message: ").strip()
        else:
            raise ValueError("Unknown mode")

    return (
        key_phrase,
        mode.lower(),
        message,
        cube_length,
        num_rotors_to_make,
        rotors_to_use,
        should_use_steganography,
        plugboard_values,
    )


def prep_string_for_encrypting(orig_message: str) -> str:
    """
    Pad the string with random pad symbols until its length is a multiple of LENGTH_OF_TRIO

    Args:
        orig_message (str): String to be prepared for encryption

    Returns:
        str: String prepared for encryption
    """
    if not orig_message:
        raise ValueError("Cannot encrypt an empty message")
    length_of_incomplete_chunk = len(orig_message) % LENGTH_OF_TRIO
    incomplete_chunk = orig_message[-length_of_incomplete_chunk:]
    message_without_incomplete_chunk = orig_message[0:-length_of_incomplete_chunk]
    complete_chunk = _pad_chunk_with_rand_pad_symbols(incomplete_chunk)
    sanitized_string = message_without_incomplete_chunk + complete_chunk
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


def rotate_slice_of_cube(cube: list[list[list[str]]], combined_seed: str) -> list[list[list[str]]]:
    """
    Rotate a slice of a 3D cube (3-dimensional array of chars) along a chosen axis.

    Args:
        cube: A 3D list representing the cube.
        combined_seed: A seed string to ensure deterministic random behavior.

    Returns:
        A new 3D list with the specified slice rotated.
    """
    axis, rotate_dir, slice_idx_to_rotate = get_independently_deterministic_random_rotor_info(
        combined_seed, ["X", "Y", "Z"], [-1, 1], len(cube) - 1
    )

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


def sanitize(raw_input: str) -> str:
    if raw_input.startswith("\\"):
        return raw_input.strip().replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return raw_input.replace("\n", "")


def split_to_human_readable_symbols(s: str, expected_number_of_graphemes: int | None = LENGTH_OF_TRIO) -> list[str]:
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
            raise ValueError(f"The input string must have a user-perceived length of {expected_number_of_graphemes}.")
    return graphemes


def _user_perceived_length(s: str) -> int:
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
