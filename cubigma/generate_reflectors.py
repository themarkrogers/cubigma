import json
import math
import os
import random

from cubigma.utils import LENGTH_OF_QUARTET, strengthen_key


def generate_reflector(sanitized_key_phrase: str, num_symbols: int) -> dict[int, int]:
    """
    Generate a deterministic reflector for a given number of symbols.

    Args:
        sanitized_key_phrase (str): The encryption key used to seed the random generator.
        num_symbols (int): The total number of symbols.

    Returns:
        dict[int, int]: A mapping of symbols to their reflected counterparts.
    """
    random.seed(sanitized_key_phrase)

    indices = list(range(num_symbols))
    random.shuffle(indices)

    reflector = {}
    for i in range(0, len(indices) - 1, 2):
        q1, q2 = indices[i], indices[i + 1]
        reflector[q1] = q2
        reflector[q2] = q1

    # Handle the last unpaired symbol, if odd number of symbols
    if len(indices) % 2 == 1:
        last = indices[-1]
        reflector[last] = last

    return reflector


def read_reflector_from_file(cube_size: int, output_dir: str = "reflectors") -> dict[int, int]:
    """
    Read a reflector from a file for a given cube size.

    Args:
        cube_size (int): The size of the cube for which to read the reflector.
        output_dir (str): Directory where the reflector files are stored.

    Returns:
        Dict[int, int]: The reflector mapping.
    """
    file_path = os.path.join(output_dir, f"reflector_{cube_size}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Reflector file for cube size {cube_size} not found at {file_path}.")

    with open(file_path, "r") as f:
        compressed_reflector = json.load(f)

    # Rehydrate the full reflector
    reflector = {}
    for k, v in compressed_reflector:
        reflector[k] = v
        reflector[v] = k

    return reflector


def write_reflector_to_file(cube_sizes: list[int], sanitized_key_phrase: str, output_dir: str = "reflectors") -> None:
    """
    Generate and write reflector mappings for multiple cube sizes to disk.

    Args:
        cube_sizes (list[int]): List of cube sizes for which to generate reflectors.
        sanitized_key_phrase (str): The encryption key used to seed the random generator.
        output_dir (str): Directory to save the reflector files.

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    for cube_size in cube_sizes:
        num_total_symbols = cube_size * cube_size * cube_size
        num_unique_quartets = math.comb(
            num_total_symbols, LENGTH_OF_QUARTET
        )  # Cube of 6 has 88_201_170, Cube of 7 has 566_685_735
        reflector = generate_reflector(sanitized_key_phrase, num_unique_quartets)

        # Compress the reflector to save space
        compressed_reflector = [(k, v) for k, v in reflector.items() if k <= v]

        file_path = os.path.join(output_dir, f"reflector_{cube_size}.json")
        with open(file_path, "w", encoding="utf-8") as reflector_file:
            json.dump(compressed_reflector, reflector_file)

        print(f"Reflector for cube size {cube_size} saved to {file_path}")


def main() -> None:
    cube_sizes = [5, 6, 7, 8, 9, 10, 11]
    key_phrase = "This is not the key_phrase that was used to create the files stored in git ;)"
    strengthened_key_phrase, bases64_encoded_salt = strengthen_key(key_phrase, salt=None)
    write_reflector_to_file(cube_sizes, strengthened_key_phrase)


if __name__ == "__main__":
    main()
