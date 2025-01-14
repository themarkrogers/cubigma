"""
This file combines the encryption in cubigma.py and the steganography in steganography.py into one handy file.
"""

import random

from cubigma.cubigma import prep_string_for_encrypting
from cubigma.cubigma import Cubigma
from cubigma.steganography import embed_chunks, get_chunks_from_image, get_image_size
from cubigma.utils import LENGTH_OF_QUARTET, pad_chunk, parse_arguments

NUM_SQUARES = 5


def _fits_in_rectangle(squares: list[int], width: int, height: int) -> bool:
    """Check if squares can fit into a rectangle of given width and height without overlapping."""
    sorted_squares = sorted(squares, reverse=True)  # Sort descending for better packing
    rectangle = [(0, 0, width, height)]  # Available space as rectangles

    for square in sorted_squares:
        side = int(square**0.5)  # Get the side length of the square
        placed = False

        for i, (x1, y1, x2, y2) in enumerate(rectangle):
            if side <= (x2 - x1) and side <= (y2 - y1):  # Check if square fits
                # Place the square and update available space
                new_rectangles = [
                    (x1 + side, y1, x2, y2),  # Right
                    (x1, y1 + side, x2, y2),  # Top
                    (x1, y1, x1 + side, y1 + side),  # Used space
                ]
                rectangle.pop(i)
                rectangle.extend(new_rectangles)
                placed = True
                break

        if not placed:
            return False

    return True


def find_five_random_squares_that_fit(
    message_length: int, image_width: int, image_height: int
) -> None | tuple[int, int, int, int, int]:
    """
    Finds five integers (a, b, c, d, e) such that:
        - a^2 + b^2 + c^2 + d^2 + e^2 >= X
        - Their areas (a^2, b^2, c^2, d^2, e^2) can fit into a rectangle of size J x K without overlapping
        - a != b != c != d != e
        - If multiple solutions exist, one solution from the smallest third of total area is returned.

    Args:
        message_length (int): The minimum sum of squares.
        image_width (int): Width of the rectangle.
        image_height (int): Height of the rectangle.

    Returns:
        None | tuple[int, int, int, int, int]: A tuple of 5 integers (a, b, c, d, e), or None if no solution is found.
    """

    solutions: list[tuple[int, int, int, int, int]] = []
    while len(solutions) < 1000:  # Generate multiple candidate solutions
        a, b, c, d, e = random.sample(range(1, min(image_width, image_height) + 1), 5)
        squares = [a**2, b**2, c**2, d**2, e**2]
        if sum(squares) >= message_length and _fits_in_rectangle(squares, image_width, image_height):
            solutions.append((a, b, c, d, e))
    if not solutions:
        return None

    # Sort solutions by total area and pick one randomly from the smallest third
    solutions.sort(key=lambda nums: sum(x**2 for x in nums))
    smallest_third = solutions[: len(solutions) // 3]
    return random.choice(smallest_third)


def split_message_according_to_numbers(square_lengths: list[int], message: str) -> list[str]:
    """
    Splits a message into parts based on the proportional lengths defined by square_lengths.

    Args:
        square_lengths (List[int]): List of integers representing lengths.
        message (str): The message to split.

    Returns:
        List[str]: A list of message parts split proportionally to square_lengths.
    """
    sum_of_lengths = sum(square_lengths)
    ratios_of_cuts = [i / float(sum_of_lengths) for i in square_lengths]
    message_length = len(message)
    message_parts: list[str] = []

    start_index = 0
    for ratio in ratios_of_cuts:
        part_length = round(ratio * message_length)
        end_index = start_index + part_length
        message_parts.append(message[start_index:end_index])
        start_index = end_index

    length_of_message_parts = sum([len(i) for i in message_parts])
    assert message_length == length_of_message_parts, "This function didn't work as expected"
    return message_parts


def encrypt_message_into_image(
    original_image_filepath: str, key_phrase: str = "", mode: str = "", message: str = ""
) -> None:
    """
    Encrypt the message using the key phrase and embed it into the image provided

    Args:
        original_image_filepath (str): Filepath of the image into which to embed the encrypted message
        key_phrase (str): Raw key phrase
        mode (str): 'encrypt' or 'decrypt
        message (str): Message to encrypt/decrypt

    Returns:
        None
    """
    cubigma = Cubigma("cube.txt")
    tuple_result = parse_arguments(key_phrase=key_phrase, mode=mode, message=message)
    (
        key_phrase,
        mode,
        clear_text_message,
        cube_length,
        num_rotors_to_make,
        rotors_to_use,
        should_use_steganography,
        plugboard_values,
    ) = tuple_result
    cubigma.prepare_machine(
        key_phrase,
        cube_length,
        num_rotors_to_make,
        rotors_to_use,
        should_use_steganography,
        plugboard_values,
        salt=None,
    )
    clear_text_message_after_plugboard = cubigma._run_message_through_plugboard(clear_text_message)
    sanitized_string = prep_string_for_encrypting(clear_text_message_after_plugboard)

    image_width, image_height = get_image_size(original_image_filepath)
    raw_chunk_sizes = find_five_random_squares_that_fit(len(sanitized_string), image_width, image_height)
    if raw_chunk_sizes is None:
        raise ValueError("No solutions found to embed provided message in provided image. Better luck next time.")
    chunk_sizes = list(raw_chunk_sizes)
    chunks = split_message_according_to_numbers(chunk_sizes, sanitized_string)

    # # "- LENGTH_OF_QUARTET" is to leave room for the prefixed order number
    # padded_chunk_length = (int(padded_length / NUM_SQUARES) - LENGTH_OF_QUARTET)

    padded_chunks = []
    for i in range(5):
        rotor_to_use = i % len(cubigma.rotors)
        padded_chunk = pad_chunk(chunks[i], chunk_sizes[i] - LENGTH_OF_QUARTET, i + 1, cubigma.rotors[rotor_to_use])
        padded_chunks.append(padded_chunk)

    # Then encrypt each chunk
    encrypted_chunks = []
    for i in range(5):
        encrypted_chunk = cubigma.encode_string(padded_chunks[i], key_phrase)
        encrypted_chunk_after_plugboard = cubigma._run_message_through_plugboard(encrypted_chunk)
        encrypted_chunks.append(encrypted_chunk_after_plugboard)
    random.shuffle(encrypted_chunks)

    embed_chunks(encrypted_chunks, original_image_filepath)


def decrypt_message_from_image(stego_image_filepath: str, key_phrase: str = "", mode: str = "") -> str:
    """
    Read the image for an embedded message, and decrypt it using the key phrase provided

    Args:
        stego_image_filepath (str): Filepath of the image to read for embedded, encrypted messages
        key_phrase (str): Raw key phrase
        mode (str): 'encrypt' or 'decrypt

    Returns:
        Decrypted message
    """
    cubigma = Cubigma("cube.txt")
    tuple_result = parse_arguments(key_phrase=key_phrase, mode=mode)
    (
        key_phrase,
        mode,
        message,
        cube_length,
        num_rotors_to_make,
        rotors_to_use,
        should_use_steganography,
        plugboard_values,
    ) = tuple_result
    salt = "Coming soon..."  # ToDo: actually get the salt from the chunks
    cubigma.prepare_machine(
        key_phrase,
        cube_length,
        num_rotors_to_make,
        rotors_to_use,
        should_use_steganography,
        plugboard_values,
        salt=salt,
    )
    chunks = get_chunks_from_image(stego_image_filepath)
    chunk_by_order_number = {}
    for chunk in chunks:
        encrypted_order_number = chunk[0:LENGTH_OF_QUARTET]
        decrypted_order_number = cubigma.decode_string(encrypted_order_number, key_phrase)
        order_number = int(decrypted_order_number)
        chunk_by_order_number[order_number] = chunk

    # Assemble the 5 chunks in order
    encrypted_noisy_message = ""
    for i in range(NUM_SQUARES):
        # Use the key to decode the first quartet in each chunk to determine assembly order
        cur_chunk = chunk_by_order_number[i]
        encrypted_noisy_message += cur_chunk[LENGTH_OF_QUARTET:]

    decrypted_message = cubigma.decrypt_message(encrypted_noisy_message, key_phrase)
    return decrypted_message


def main() -> None:
    """
    Used for testing.

    Returns:
        None
    """
    key_phrase = "Death and Taxes"
    mode = "ENCRYPT"
    message = "This is cool!"
    print("Encrypting...")
    encrypt_message_into_image("kitten.jpg.png", key_phrase=key_phrase, mode=mode, message=message)
    print("Done encrypting!")
    print("Decrypting...")
    mode = "DECRYPT"
    decrypted_message = decrypt_message_from_image("kitten.jpg.data.png", key_phrase=key_phrase, mode=mode)
    print("Done decrypting!")
    print("Found message:\n")
    print(decrypted_message)


if __name__ == "__main__":
    main()
