"""
This file combines the encryption in cubigma.py and the steganography in steganography.py into one handy file.
"""

from itertools import combinations_with_replacement
import math
import random

from cubigma.cubigma import prep_string_for_encrypting
from cubigma.cubigma import Cubigma
from cubigma.steganography import embed_chunks, get_chunks_from_image
from cubigma.utils import read_config, LENGTH_OF_QUARTET, NOISE_SYMBOL

config = read_config()
SYMBOLS_PER_LINE = config["SYMBOLS_PER_LINE"]
LINES_PER_BLOCK = config["LINES_PER_BLOCK"]
NUM_BLOCKS = config["NUM_BLOCKS"]

NUM_SQUARES = 5


def smallest_sum_of_five_squares_greater_than_or_equal_to(number: int) -> int:
    """
    Find the smallest sum of any 5 square numbers, each a multiple of 4, greater than or equal to the given number.

    Args:
        number (int): The target number.

    Returns:
        int: The smallest sum of 5 squares meeting the criteria.
    """
    # Generate a list of squares that are multiples of 4
    squares = []
    n = 3  # Do not consider 1, 2, or 4; we need >4, length of order number quartet added later
    while True:
        square = math.pow(n, 2)
        if square % LENGTH_OF_QUARTET == 0:  # Ensure the square is a multiple of 4
            squares.append(square)
        if len(squares) >= 1:
            break
        n += 1

    # Generate combinations of 5 squares
    smallest_sum = float("inf")
    for combination in combinations_with_replacement(squares, NUM_SQUARES):
        total = sum(combination)
        if total >= number:
            smallest_sum = min(smallest_sum, total)
    return smallest_sum


def encrypt_message_into_image(key_phrase: str, clear_text_message: str, original_image_filepath: str) -> None:
    """
    Encrypt the message using the key phrase and embed it into the image provided

    Args:
        key_phrase (str): The key phrase to use to encrypt
        clear_text_message (str): The plain text message to encrypt
        original_image_filepath (str): Filepath of the image into which to embed the encrypted message

    Returns:
        None
    """
    cubigma = Cubigma("cuboid.txt")
    cubigma.prepare_cuboid_with_key_phrase(key_phrase)
    sanitized_string = prep_string_for_encrypting(clear_text_message)
    string_length = len(sanitized_string)
    one_fifth = math.ceil(string_length / float(NUM_SQUARES))

    start_idx1 = 0 * one_fifth
    idx_1_2 = 1 * one_fifth
    idx_2_3 = 2 * one_fifth
    idx_3_4 = 3 * one_fifth
    idx_4_5 = 4 * one_fifth
    chunk1 = sanitized_string[start_idx1:idx_1_2]
    chunk2 = sanitized_string[idx_1_2:idx_2_3]
    chunk3 = sanitized_string[idx_2_3:idx_3_4]
    chunk4 = sanitized_string[idx_3_4:idx_4_5]
    chunk5 = sanitized_string[idx_4_5:]

    padded_length = smallest_sum_of_five_squares_greater_than_or_equal_to(len(sanitized_string))

    # "- LENGTH_OF_QUARTET" is to leave room for the prefixed order number
    padded_chunk_length = (int(padded_length / NUM_SQUARES) - LENGTH_OF_QUARTET)

    padded_chunk1 = cubigma.pad_chunk(chunk1, padded_chunk_length, 1)
    padded_chunk2 = cubigma.pad_chunk(chunk2, padded_chunk_length, 2)
    padded_chunk3 = cubigma.pad_chunk(chunk3, padded_chunk_length, 3)
    padded_chunk4 = cubigma.pad_chunk(chunk4, padded_chunk_length, 4)
    padded_chunk5 = cubigma.pad_chunk(chunk5, padded_chunk_length, 5)

    # Then encrypt each chunk
    encrypted_chunk1 = cubigma.encode_string(padded_chunk1)
    encrypted_chunk2 = cubigma.encode_string(padded_chunk2)
    encrypted_chunk3 = cubigma.encode_string(padded_chunk3)
    encrypted_chunk4 = cubigma.encode_string(padded_chunk4)
    encrypted_chunk5 = cubigma.encode_string(padded_chunk5)

    encrypted_chunks = [encrypted_chunk1, encrypted_chunk2, encrypted_chunk3, encrypted_chunk4, encrypted_chunk5]
    random.shuffle(encrypted_chunks)

    embed_chunks(encrypted_chunks, original_image_filepath)


def decrypt_message_from_image(key_phrase: str, stego_image_filepath: str) -> str:
    """
    Read the image for an embedded message, and decrypt it using the key phrase provided

    Args:
        key_phrase (str): The key phrase to use to encrypt
        stego_image_filepath (str): Filepath of the image to read for embedded, encrypted messages

    Returns:
        Decrypted message
    """
    cubigma = Cubigma("cuboid.txt")
    cubigma.prepare_cuboid_with_key_phrase(key_phrase)
    chunks = get_chunks_from_image(stego_image_filepath)
    chunk_by_order_number = {}
    for chunk in chunks:
        encrypted_order_number = chunk[0:LENGTH_OF_QUARTET]
        decrypted_order_number = cubigma.decode_string(encrypted_order_number)
        order_number = int(decrypted_order_number)
        chunk_by_order_number[order_number] = chunk

    # Assemble the 5 chunks in order
    encrypted_noisy_message = ""
    for i in range(NUM_SQUARES):
        # Use the key to decode the first quartet in each chunk to determine assembly order
        cur_chunk = chunk_by_order_number[i]
        encrypted_noisy_message += cur_chunk[LENGTH_OF_QUARTET:]

    # Remove all quartets with the TOTAL_NOISE characters
    decrypted_message = ""
    for i in range(0, len(encrypted_noisy_message), LENGTH_OF_QUARTET):
        end_idx = i + LENGTH_OF_QUARTET
        encrypted_chunk = encrypted_noisy_message[i:end_idx]
        decrypted_chunk = cubigma.decode_string(encrypted_chunk)
        if NOISE_SYMBOL not in decrypted_chunk:
            decrypted_message += decrypted_chunk
    return decrypted_message


def main() -> None:
    """
    Used for testing.

    Returns:
        None
    """
    key_phrase = "Death and Taxes"
    print("Encrypting...")
    encrypt_message_into_image(key_phrase, "This is cool!", "kitten.jpg.png")
    print("Done encrypting!")
    print("Decrypting...")
    decrypted_message = decrypt_message_from_image(key_phrase, "kitten.jpg.data.png")
    print("Done decrypting!")
    print("Found message:\n")
    print(decrypted_message)


if __name__ == "__main__":
    main()
