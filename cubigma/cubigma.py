"""
This file is used to encrypt and decrypt messages using the prepared cuboid.txt file.
This code implements the Cubigma encryption algorithm.
"""

import math
import random

from cubigma.utils import (
# from utils import (
    LENGTH_OF_QUARTET,
    NOISE_SYMBOL,
    generate_reflector,
    generate_rotors,
    get_opposite_corners,
    get_prefix_order_number_quartet,
    get_random_noise_chunk,
    index_to_quartet,
    pad_chunk_with_rand_pad_symbols,
    parse_arguments,
    prep_string_for_encrypting,
    prepare_cuboid_with_key_phrase,
    quartet_to_index,
    sanitize,
    strengthen_key,
    user_perceived_length,
)

NUM_BLOCKS = 7  # X
LINES_PER_BLOCK = 7  # Y
SYMBOLS_PER_LINE = 7  # Z

NUM_TOTAL_SYMBOLS = NUM_BLOCKS * LINES_PER_BLOCK * SYMBOLS_PER_LINE
NUM_UNIQUE_QUARTETS = math.comb(NUM_TOTAL_SYMBOLS, LENGTH_OF_QUARTET)


class Cubigma:
    _characters_filepath: str
    _cuboid_filepath: str
    _is_machine_prepared: bool = False
    _num_quartets_encoded = 0
    _symbols: list[str]
    rotors: list[list[list[list[str]]]]
    reflector: dict[int, int]

    def __init__(self, characters_filepath: str = "characters.txt", cuboid_filepath: str = "cuboid.txt"):
        self._characters_filepath = characters_filepath
        self._cuboid_filepath = cuboid_filepath
        self._is_machine_prepared = False

    def _run_quartet_through_rotors(self, char_quartet: str, rotors: list[list[list[list[str]]]]) -> str:
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
            encrypted_indices = get_opposite_corners(
                orig_indices[0],
                orig_indices[1],
                orig_indices[2],
                orig_indices[3],
                NUM_BLOCKS,
                LINES_PER_BLOCK,
                SYMBOLS_PER_LINE,
                num_quartets_encoded
            )
            num_quartets_encoded += 1
            encrypted_char_1 = self._get_chars_for_coordinates(encrypted_indices[0], rotor)
            encrypted_char_2 = self._get_chars_for_coordinates(encrypted_indices[1], rotor)
            encrypted_char_3 = self._get_chars_for_coordinates(encrypted_indices[2], rotor)
            encrypted_char_4 = self._get_chars_for_coordinates(encrypted_indices[3], rotor)
            encrypted_quartet = "".join([encrypted_char_1, encrypted_char_2, encrypted_char_3, encrypted_char_4])
            cur_quartet = encrypted_quartet
        return cur_quartet

    def _run_quartet_through_reflector(self, char_quartet) -> str:
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call prepare_machine(key_phrase) before running quartet through reflector"
            )
        quartet_index = quartet_to_index(char_quartet, self._symbols)
        reflected_index = self.reflector[quartet_index]  # Reflect the index
        reflected_quartet = index_to_quartet(reflected_index, self._symbols)
        return reflected_quartet

    def _get_encrypted_letter_quartet(self, char_quartet: str) -> str:
        partially_encrypted_quartet_1 = self._run_quartet_through_rotors(char_quartet, self.rotors)
        partially_encrypted_quartet_2 = self._run_quartet_through_reflector(partially_encrypted_quartet_1)
        encrypted_quartet = self._run_quartet_through_rotors(partially_encrypted_quartet_2, list(reversed(self.rotors)))
        return encrypted_quartet

    def _read_characters_file(self) -> list[str]:
        with open(self._characters_filepath, "r", encoding="utf-8") as line_count_file:
            num_symbols_prepared = sum(1 for _ in line_count_file)

        symbols_to_load = SYMBOLS_PER_LINE * LINES_PER_BLOCK * NUM_BLOCKS
        symbols_loaded = 0
        if symbols_to_load > num_symbols_prepared:
            raise ValueError(
                f"Not enough symbols are prepared. {num_symbols_prepared} symbols prepared. "
                + f"Requested a cuboid with {symbols_to_load} symbols. "
            )
        symbols: list[str] = []
        with open(self._characters_filepath, "r", encoding="utf-8") as file:
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

    def _read_cuboid_from_disk(self) -> list[list[list[str]]]:
        playfair_cuboid = []
        current_frame = []
        with open(self._cuboid_filepath, "r", encoding="utf-8-sig") as cuboid_file:
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
        return playfair_cuboid

    def _write_cuboid_file(
        self,
        symbols: list[str],
        num_blocks: int = NUM_BLOCKS,
        lines_per_block: int = LINES_PER_BLOCK,
        symbols_per_line: int = SYMBOLS_PER_LINE,
    ) -> None:
        symbols_per_block = symbols_per_line * lines_per_block
        output_lines = []
        for block in range(num_blocks):
            for row in range(lines_per_block):
                start_idx = block * symbols_per_block + row * symbols_per_line
                end_idx = block * symbols_per_block + (row + 1) * symbols_per_line
                line = "".join(symbols[start_idx:end_idx])
                if user_perceived_length(line) != symbols_per_line:
                    raise ValueError("Something has failed")
                sanitized_line = line.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
                output_lines.append(sanitized_line)
            output_lines.append("")  # Add an empty line between blocks
        with open(self._cuboid_filepath, "w", encoding="utf-8") as file:
            file.write("\n".join(output_lines))

    def decode_string(self, encrypted_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            encrypted_message (str): Encrypted message

        Returns:
            str: Decrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encoding or decoding"
            )
        raw_decrypted_message = self.encode_string(encrypted_message)
        decrypted_message = raw_decrypted_message.replace("", "").replace("", "").replace("", "")
        return decrypted_message

    def decrypt_message(self, encrypted_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            encrypted_message (str): Encrypted message

        Returns:
            str: Decrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encrypting or decrypting"
            )

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
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encoding or decoding"
            )
        assert len(sanitized_message) % LENGTH_OF_QUARTET == 0, "Message is not properly sanitized!"
        encrypted_message = ""
        for i in range(0, len(sanitized_message), LENGTH_OF_QUARTET):
            end_idx = i + LENGTH_OF_QUARTET
            orig_chunk = sanitized_message[i:end_idx]
            encrypted_chunk = self._get_encrypted_letter_quartet(orig_chunk)
            encrypted_message += encrypted_chunk
        return encrypted_message

    def encrypt_message(self, clear_text_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            clear_text_message (str): Message to encrypt

        Returns:
            str: Encrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encrypting or decrypting"
            )
        sanitized_string = prep_string_for_encrypting(clear_text_message)
        encrypted_message = self.encode_string(sanitized_string)
        return encrypted_message

    def pad_chunk(self, chunk: str, padded_chunk_length: int, chunk_order_number: int, rotor: list[list[list[str]]]) -> str:
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
            random_noise_chunk = get_random_noise_chunk(rotor)
            padded_chunk += random_noise_chunk
        prefix_order_number_quartet = get_prefix_order_number_quartet(chunk_order_number)
        result = prefix_order_number_quartet + padded_chunk
        return result

    def prepare_machine(
        self,
        key_phrase: str,
        cuboid_height: int = NUM_BLOCKS,
        cuboid_length: int = LINES_PER_BLOCK,
        cuboid_width: int = SYMBOLS_PER_LINE,
    ) -> None:
        # Set up user-configurable parameters (like the plug board)
        self._symbols = self._read_characters_file()
        self._write_cuboid_file(
            self._symbols, num_blocks=cuboid_height, lines_per_block=cuboid_length, symbols_per_line=cuboid_width
        )
        raw_cuboid = self._read_cuboid_from_disk()
        cuboid = prepare_cuboid_with_key_phrase(key_phrase, raw_cuboid)
        
        key_phrase_bytes, salt_used = strengthen_key(key_phrase)
        sanitized_key_phrase = key_phrase_bytes.decode("utf-8")

        # Set up the rotors and the reflector
        rotors = generate_rotors(sanitized_key_phrase, cuboid)
        reflector = generate_reflector(sanitized_key_phrase, NUM_UNIQUE_QUARTETS)
        self.rotors = rotors
        self.reflector = reflector
        self._is_machine_prepared = True


def main() -> None:
    """
    Entrypoint for the cubigma project.

    Returns:
        None
    """
    cubigma = Cubigma("characters.txt", "cuboid.txt")

    # ToDo: Add functionality for salt. Alice generates a random salt when encrypting the message. Alice then transmits
    # the encrypted message AND THE CLEARTEXT SALT to Bob.
    # Maybe:
    # Don't confuse the users with the notion of a salt
    # Encrypting: The salt is always 16-bytes long, and always prepended to the encrypted message
    # Steganography: Account for an extra 16-bits when calculating the sum_of_squares

    # key_phrase = "Rumpelstiltskin"
    # clear_text_message = "This is cool!"
    key_phrase, mode, message = parse_arguments()
    cubigma.prepare_machine(key_phrase)

    if mode == "encrypt":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(message)
        print(f"{encrypted_message=}")
    elif mode == "decrypt":
        encrypted_message = message
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(message)
        print(f"{decrypted_message=}")
    else:  # mode == "both":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(clear_text_message)
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(encrypted_message)
        print(f"{decrypted_message=}")


if __name__ == "__main__":
    main()
