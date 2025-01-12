"""
This file is used to encrypt and decrypt messages using the prepared cuboid.txt file.
This is Step 2 (the main step) in The Cubigma encryption algorithm.
"""

import math
import random

from cubigma.utils import user_perceived_length, LENGTH_OF_QUARTET, NOISE_SYMBOL
from cubigma.utils import get_opposite_corners, get_prefix_order_number_quartet, pad_chunk_with_rand_pad_symbols
from cubigma.utils import remove_duplicate_letters, prep_string_for_encrypting, sanitize, parse_arguments, prepare_cuboid_with_key_phrase
# from utils import user_perceived_length, LENGTH_OF_QUARTET, NOISE_SYMBOL

NUM_BLOCKS = 7  # X
LINES_PER_BLOCK = 7  # Y
SYMBOLS_PER_LINE = 7  # Z

NUM_TOTAL_SYMBOLS = NUM_BLOCKS * LINES_PER_BLOCK * SYMBOLS_PER_LINE
NUM_UNIQUE_QUARTETS = math.comb(NUM_TOTAL_SYMBOLS, LENGTH_OF_QUARTET)

# Keyboard (input)
# Input wheel
# 3 Rotors (clever scramblers)
#   * Moved after each encoding
# Reflector (different scrambler, pairwise)
#   * Back through the 3 rotors, differently
# Plugboard (user configurable, swaps pairs of letters)
# Lampboard (output)



class Cubigma:
    characters_filepath: str
    cuboid_filepath: str
    playfair_cuboid: list[list[list[str]]]
    playfair_cuboid: list[list[list[str]]]
    playfair_cuboid: list[list[list[str]]]
    playfair_cuboid: list[list[list[str]]]

    def __init__(self, characters_filepath: str, cuboid_filepath: str):
        self.characters_filepath = characters_filepath
        self.cuboid_filepath = cuboid_filepath

    def _get_chars_for_coordinates(self, coordinate: tuple[int, int, int]) -> str:
        x, y, z = coordinate
        return self.playfair_cuboid[x][y][z]

    def _get_encrypted_letter_quartet(self, char_quartet: str) -> str:
        indices_by_char = {}
        for frame_idx, cur_frame in enumerate(self.playfair_cuboid):
            for row_idx, cur_line in enumerate(cur_frame):
                if any(char in cur_line for char in char_quartet):
                    if char_quartet[0] in cur_line:
                        indices_by_char[char_quartet[0]] = (frame_idx, row_idx, cur_line.index(char_quartet[0]))
                    if char_quartet[1] in cur_line:
                        indices_by_char[char_quartet[1]] = (frame_idx, row_idx, cur_line.index(char_quartet[1]))
                    if char_quartet[2] in cur_line:
                        indices_by_char[char_quartet[2]] = (frame_idx, row_idx, cur_line.index(char_quartet[2]))
                    if char_quartet[3] in cur_line:
                        indices_by_char[char_quartet[3]] = (frame_idx, row_idx, cur_line.index(char_quartet[3]))
        orig_indices = []
        for cur_char in char_quartet:
            orig_indices.append(indices_by_char[cur_char])
        encrypted_indices = get_opposite_corners(orig_indices[0], orig_indices[1], orig_indices[2], orig_indices[3], NUM_BLOCKS, LINES_PER_BLOCK, SYMBOLS_PER_LINE)
        encrypted_char_one = self._get_chars_for_coordinates(encrypted_indices[0])
        encrypted_char_two = self._get_chars_for_coordinates(encrypted_indices[1])
        encrypted_char_three = self._get_chars_for_coordinates(encrypted_indices[2])
        encrypted_char_four = self._get_chars_for_coordinates(encrypted_indices[3])
        encrypted_quartet = "".join([encrypted_char_one, encrypted_char_two, encrypted_char_three, encrypted_char_four])
        return encrypted_quartet

    def _get_random_noise_chunk(self) -> str:
        noise_quartet_symbols = [NOISE_SYMBOL]
        while len(noise_quartet_symbols) < LENGTH_OF_QUARTET:
            coordinate = (
                random.randint(0, NUM_BLOCKS - 1),
                random.randint(0, LINES_PER_BLOCK - 1),
                random.randint(0, SYMBOLS_PER_LINE - 1),
            )
            x, y, z = coordinate
            found_symbol = self.playfair_cuboid[x][y][z]
            if found_symbol not in noise_quartet_symbols:
                noise_quartet_symbols.append(found_symbol)
        random.shuffle(noise_quartet_symbols)
        return "".join(noise_quartet_symbols)

    def _read_characters_file(self) -> list[str]:
        with open(self.characters_filepath, "r", encoding="utf-8") as line_count_file:
            num_symbols_prepared = sum(1 for _ in line_count_file)

        symbols_to_load = SYMBOLS_PER_LINE * LINES_PER_BLOCK * NUM_BLOCKS
        symbols_loaded = 0
        if symbols_to_load > num_symbols_prepared:
            raise ValueError(
                f"Not enough symbols are prepared. {num_symbols_prepared} symbols prepared. "
                + f"Requested a cuboid with {symbols_to_load} symbols. "
            )
        symbols = []
        with open(self.characters_filepath, "r", encoding="utf-8") as file:
            for line in file.readlines():
                len_before = len(symbols)
                found_symbol = sanitize(line)
                symbols.append(found_symbol)
                len_after = len(symbols)
                if len_before == len_after:
                    print(f"Duplicate symbol found: {found_symbol}")
                symbols_loaded += 1
                if symbols_loaded >= symbols_to_load:
                    break
        symbols_per_block = SYMBOLS_PER_LINE * LINES_PER_BLOCK
        total_num_of_symbols = symbols_per_block * NUM_BLOCKS

        if len(symbols) != total_num_of_symbols:
            raise ValueError(
                f"The file must contain exactly {total_num_of_symbols} symbols, one per line. Found {len(symbols)}"
            )

        # Reverse, so the least common symbols are first; this helps entropy when loading the key phrase
        symbols = list(reversed(symbols))
        return symbols

    def _read_cuboid_from_disk(self) -> None:
        playfair_cuboid = []
        current_frame = []
        with open(self.cuboid_filepath, "r", encoding="utf-8-sig") as cuboid_file:
            for line in cuboid_file.readlines():
                if line != "\n":
                    sanitized_line = line.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
                    if sanitized_line.endswith("\n"):
                        trimmed_line = sanitized_line[0:-1]
                    else:
                        trimmed_line = sanitized_line
                    if user_perceived_length(trimmed_line) > SYMBOLS_PER_LINE:
                        raise ValueError(
                            "String have already been formatted to a length of 6. This error is unexpected."
                        )
                    current_frame.append(list(trimmed_line))
                if len(current_frame) >= LINES_PER_BLOCK:
                    playfair_cuboid.append(current_frame)
                    current_frame = []
        self.playfair_cuboid = playfair_cuboid

    def _write_cuboid_file(self, symbols: list[str]) -> None:
        symbols_per_block = SYMBOLS_PER_LINE * LINES_PER_BLOCK
        output_lines = []
        for block in range(NUM_BLOCKS):
            for row in range(LINES_PER_BLOCK):
                start_idx = block * symbols_per_block + row * SYMBOLS_PER_LINE
                end_idx = block * symbols_per_block + (row + 1) * SYMBOLS_PER_LINE
                line = "".join(symbols[start_idx:end_idx])
                if user_perceived_length(line) != SYMBOLS_PER_LINE:
                    raise ValueError("Something has failed")
                sanitized_line = line.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
                output_lines.append(sanitized_line)
            output_lines.append("")  # Add an empty line between blocks
        with open(self.cuboid_filepath, "w", encoding="utf-8") as file:
            file.write("\n".join(output_lines))

    def decode_string(self, encrypted_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            encrypted_message (str): Encrypted message

        Returns:
            str: Decrypted string
        """
        raw_decrypted_message = self.encode_string(encrypted_message)
        decrypted_message = raw_decrypted_message.replace("", "").replace("", "").replace("", "")
        return decrypted_message

    def decrypt_message(self, key_phrase: str, encrypted_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            key_phrase (str): Key phrase used to decrypt the message
            encrypted_message (str): Encrypted message

        Returns:
            str: Decrypted string
        """
        self._read_cuboid_from_disk()
        prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)

        # Remove all quartets with the TOTAL_NOISE characters
        decrypted_message = ""
        for i in range(0, len(encrypted_message), LENGTH_OF_QUARTET):
            end_idx = i + LENGTH_OF_QUARTET
            encrypted_chunk = encrypted_message[i:end_idx]
            decrypted_chunk = self.decode_string(encrypted_chunk)
            if NOISE_SYMBOL not in decrypted_chunk:
                decrypted_message += decrypted_chunk
        return decrypted_message

    def encode_string(self, sanitized_message: str) -> str:
        """
        Encrypt the message using the playfair cuboid

        Args:
            sanitized_message (str): String prepared for encryption

        Returns:
            str: Encrypted string
        """
        assert len(sanitized_message) % LENGTH_OF_QUARTET == 0, "Message is not properly sanitized!"
        encrypted_message = ""
        for i in range(0, len(sanitized_message), LENGTH_OF_QUARTET):
            end_idx = i + LENGTH_OF_QUARTET
            orig_chunk = sanitized_message[i:end_idx]
            encrypted_chunk = self._get_encrypted_letter_quartet(orig_chunk)
            encrypted_message += encrypted_chunk
        return encrypted_message

    def encrypt_message(self, key_phrase: str, clear_text_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            key_phrase (str): Key phrase used to encrypt the message
            clear_text_message (str): Message to encrypt

        Returns:
            str: Encrypted string
        """
        self._read_cuboid_from_disk()
        prepare_cuboid_with_key_phrase(key_phrase, self.playfair_cuboid)
        sanitized_string = prep_string_for_encrypting(clear_text_message)
        encrypted_message = self.encode_string(sanitized_string)
        return encrypted_message

    def pad_chunk(self, chunk: str, padded_chunk_length: int, chunk_order_number: int) -> str:
        """
        Pad an encrypted message chunk

        Args:
            chunk (str): Encrypted message chunk to pad
            padded_chunk_length (int): Desired chunk length
            chunk_order_number (int): Which chunk is this (i.e. 1-5)?

        Returns:
            str: Padded chunk
        """
        padded_chunk = chunk
        while len(padded_chunk) < padded_chunk_length:
            if len(padded_chunk) % LENGTH_OF_QUARTET != 0:
                padded_chunk = pad_chunk_with_rand_pad_symbols(padded_chunk)
            random_noise_chunk = self._get_random_noise_chunk()
            padded_chunk += random_noise_chunk
        prefix_order_number_quartet = get_prefix_order_number_quartet(chunk_order_number)
        result = prefix_order_number_quartet + padded_chunk
        return result

    def reformat_characters(self) -> None:
        """
        Convert characters.txt into cuboid.txt based on the three constants defined in config.json.
        This is Step 1 in The Cubigma encryption algorithm.

        Returns:
            None
        """
        symbols = self._read_characters_file()
        self._write_cuboid_file(symbols)
        print(f"File successfully shuffled and written to: {self.cuboid_filepath}")


def main() -> None:
    """
    Entrypoint for the cubigma project.

    Returns:
        None
    """
    cubigma = Cubigma("characters.txt", "cuboid.txt")
    cubigma.reformat_characters()

    #ToDo: Add functionality for salt. Alice generates a random salt when encrypting the message. Alice then transmits
    # the encrypted message AND THE CLEARTEXT SALT to Bob.
    # Maybe:
    # Don't confuse the users with the notion of a salt
    # Encrypting: The salt is always 16-bytes long, and always prepended to the encrypted message
    # Steganography: Account for an extra 16-bits when calculating the sum_of_squares


    # key_phrase = "Rumpelstiltskin"
    # clear_text_message = "This is cool!"
    key_phrase, mode, message = parse_arguments()
    if mode == "encrypt":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(key_phrase, message)
        print(f"{encrypted_message=}")
    elif mode == "decrypt":
        encrypted_message = message
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(key_phrase, message)
        print(f"{decrypted_message=}")
    else:  # mode == "both":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(key_phrase, clear_text_message)
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(key_phrase, encrypted_message)
        print(f"{decrypted_message=}")


if __name__ == "__main__":
    main()
