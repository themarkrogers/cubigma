"""
This file is used to encrypt and decrypt messages using the prepared cube.txt file.
This code implements the Cubigma encryption algorithm.
"""

import math

from cubigma.utils import (
    # from utils import (
    LENGTH_OF_QUARTET,
    NOISE_SYMBOL,
    generate_reflector,
    generate_rotors,
    get_chars_for_coordinates,
    get_opposite_corners,
    index_to_quartet,
    parse_arguments,
    prep_string_for_encrypting,
    quartet_to_index,
    sanitize,
    split_to_human_readable_symbols,
    strengthen_key,
    user_perceived_length,
)


class Cubigma:
    _characters_filepath: str
    _cube_filepath: str
    _is_machine_prepared: bool = False
    _is_using_steganography: bool = False
    _num_quartets_encoded = 0
    _symbols: list[str]
    rotors: list[list[list[list[str]]]]
    reflector: dict[int, int]

    def __init__(self, characters_filepath: str = "characters.txt", cube_filepath: str = "cube.txt"):
        self._characters_filepath = characters_filepath
        self._cube_filepath = cube_filepath
        self._is_machine_prepared = False

    def _run_quartet_through_reflector(self, char_quartet) -> str:
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call prepare_machine(key_phrase) before running quartet through reflector"
            )
        quartet_index = quartet_to_index(char_quartet, self._symbols)
        reflected_index = self.reflector[quartet_index]  # Reflect the index
        reflected_quartet = index_to_quartet(reflected_index, self._symbols)
        return reflected_quartet

    def _get_encrypted_letter_quartet(self, char_quartet: str, key_phrase: str) -> str:
        partially_encrypted_quartet_1 = self._run_quartet_through_rotors(char_quartet, self.rotors, key_phrase)
        partially_encrypted_quartet_2 = self._run_quartet_through_reflector(partially_encrypted_quartet_1)
        encrypted_quartet = self._run_quartet_through_rotors(
            partially_encrypted_quartet_2, list(reversed(self.rotors)), key_phrase
        )
        return encrypted_quartet

    def _run_quartet_through_rotors(
        self, char_quartet: str, rotors: list[list[list[list[str]]]], key_phrase: str
    ) -> str:
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
            encrypted_indices = get_opposite_corners(
                orig_indices[0],
                orig_indices[1],
                orig_indices[2],
                orig_indices[3],
                num_blocks,
                lines_per_block,
                symbols_per_line,
                key_phrase,
                self._num_quartets_encoded,
            )
            self._num_quartets_encoded += 1
            encrypted_char_1 = get_chars_for_coordinates(encrypted_indices[0], rotor)
            encrypted_char_2 = get_chars_for_coordinates(encrypted_indices[1], rotor)
            encrypted_char_3 = get_chars_for_coordinates(encrypted_indices[2], rotor)
            encrypted_char_4 = get_chars_for_coordinates(encrypted_indices[3], rotor)
            encrypted_quartet = "".join([encrypted_char_1, encrypted_char_2, encrypted_char_3, encrypted_char_4])
            cur_quartet = encrypted_quartet
        return cur_quartet

    def _read_characters_file(self, cube_length: int) -> list[str]:
        with open(self._characters_filepath, "r", encoding="utf-8") as line_count_file:
            num_symbols_prepared = sum(1 for _ in line_count_file)

        num_blocks = cube_length
        line_per_block = cube_length
        symbols_per_line = cube_length
        symbols_to_load = symbols_per_line * line_per_block * num_blocks
        symbols_loaded = 0
        if symbols_to_load > num_symbols_prepared:
            raise ValueError(
                f"Not enough symbols are prepared. {num_symbols_prepared} symbols prepared. "
                + f"Requested a cube with {symbols_to_load} symbols. "
            )
        symbols: list[str] = []
        unique_symbols: set[str] = set()
        with open(self._characters_filepath, "r", encoding="utf-8") as file:
            for line in file.readlines():
                sanitized_line = sanitize(line)
                for visible_symbol in split_to_human_readable_symbols(
                    sanitized_line, expected_number_of_graphemes=None
                ):
                    len_before = len(unique_symbols)
                    unique_symbols.add(visible_symbol)
                    len_after = len(unique_symbols)
                    if len_before == len_after:
                        print(f"Duplicate symbol found: {visible_symbol}")
                    symbols.append(visible_symbol)
                    symbols_loaded += 1
                    if symbols_loaded >= symbols_to_load:
                        break
        symbols_per_block = symbols_per_line * line_per_block
        total_num_of_symbols = symbols_per_block * num_blocks

        if len(symbols) != total_num_of_symbols:
            msg = f"The file must contain exactly {total_num_of_symbols} symbols, one per line. Found {len(symbols)}"
            raise ValueError(msg)

        # Reverse, so the least common symbols are first; this helps entropy when loading the key phrase
        symbols = list(reversed(list(symbols)))
        return symbols

    def _read_cube_from_disk(self, cube_length: int) -> list[list[list[str]]]:
        line_per_block = cube_length
        symbols_per_line = cube_length
        playfair_cube = []
        current_frame = []
        with open(self._cube_filepath, "r", encoding="utf-8-sig") as cube_file:
            for line in cube_file.readlines():
                if line != "\n":
                    sanitized_line = line.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
                    if sanitized_line.endswith("\n"):
                        trimmed_line = sanitized_line[0:-1]
                    else:
                        trimmed_line = sanitized_line
                    visible_length = user_perceived_length(trimmed_line)
                    if visible_length != symbols_per_line:
                        raise ValueError(
                            "String have already been formatted to a length of 6. This error is unexpected."
                        )
                    current_frame.append(list(trimmed_line))
                if len(current_frame) >= line_per_block:
                    playfair_cube.append(current_frame)
                    current_frame = []
        return playfair_cube

    def _write_cube_file(
        self,
        symbols: list[str],
        num_blocks: int = -1,
        lines_per_block: int = -1,
        symbols_per_line: int = -1,
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
        with open(self._cube_filepath, "w", encoding="utf-8") as file:
            file.write("\n".join(output_lines))

    def decode_string(self, encrypted_message: str, key_phrase: str) -> str:
        """
        Decrypt the message using the playfair cube

        Args:
            encrypted_message (str): Encrypted message
            key_phrase (str): Secret key phrase

        Returns:
            str: Decrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encoding or decoding"
            )
        raw_decrypted_message = self.encode_string(encrypted_message, key_phrase)
        decrypted_message = raw_decrypted_message.replace("", "").replace("", "").replace("", "")
        return decrypted_message

    def decrypt_message(self, encrypted_message: str, key_phrase: str) -> str:
        """
        Decrypt the message using the playfair cube

        Args:
            encrypted_message (str): Encrypted message
            key_phrase (str): Secret key phrase

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
            decrypted_chunk = self.decode_string(encrypted_chunk, key_phrase)
            if NOISE_SYMBOL not in decrypted_chunk:
                decrypted_message += decrypted_chunk
        return decrypted_message

    def encode_string(self, sanitized_message: str, key_phrase: str) -> str:
        """
        Encrypt the message using the playfair cube

        Args:
            sanitized_message (str): String prepared for encryption
            key_phrase (str): Secret key phrase

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
            encrypted_chunk = self._get_encrypted_letter_quartet(orig_chunk, key_phrase)
            encrypted_message += encrypted_chunk
        return encrypted_message

    def encrypt_message(self, clear_text_message: str, key_phrase: str) -> str:
        """
        Decrypt the message using the playfair cube

        Args:
            clear_text_message (str): Message to encrypt
            key_phrase (str): Secret key phrase

        Returns:
            str: Encrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encrypting or decrypting"
            )
        sanitized_string = prep_string_for_encrypting(clear_text_message)
        encrypted_message = self.encode_string(sanitized_string, key_phrase)
        return encrypted_message

    def prepare_machine(
        self,
        key_phrase: str,
        cube_length: int,
        num_rotors_to_make: int,
        rotors_to_use: list[int],
        should_use_steganography: bool,
    ) -> None:
        # Set up user-configurable parameters (similar to configuring the plug board on an Enigma machine)
        self._symbols = self._read_characters_file(cube_length)
        self._write_cube_file(
            self._symbols, num_blocks=cube_length, lines_per_block=cube_length, symbols_per_line=cube_length
        )
        raw_cube = self._read_cube_from_disk(cube_length)

        key_phrase_bytes, salt_used = strengthen_key(key_phrase)
        sanitized_key_phrase = key_phrase_bytes.decode("utf-8")
        for character in split_to_human_readable_symbols(sanitized_key_phrase):
            if character not in self._symbols:
                raise ValueError("Key was strengthened to include an invalid character")

        # Set up the rotors and the reflector
        rotors = generate_rotors(
            sanitized_key_phrase, raw_cube, num_rotors_to_make=num_rotors_to_make, rotors_to_use=rotors_to_use
        )
        num_total_symbols = cube_length * cube_length * cube_length
        num_unique_quartets = math.comb(num_total_symbols, LENGTH_OF_QUARTET)
        reflector = generate_reflector(sanitized_key_phrase, num_unique_quartets)
        self.rotors = rotors
        self.reflector = reflector
        self._is_using_steganography = should_use_steganography
        self._is_machine_prepared = True


def main() -> None:
    """
    Entrypoint for the cubigma project.

    Returns:
        None
    """
    cubigma = Cubigma("characters.txt", "cube.txt")

    # ToDo: Add functionality for salt. Alice generates a random salt when encrypting the message. Alice then transmits
    # the encrypted message AND THE CLEARTEXT SALT to Bob.
    # Maybe:
    # Don't confuse the users with the notion of a salt
    # Encrypting: The salt is always 16-bytes long, and always prepended to the encrypted message
    # Steganography: Account for an extra 16-bits when calculating the sum_of_squares

    # key_phrase = "Rumpelstiltskin"
    # clear_text_message = "This is cool!"
    tuple_result = parse_arguments()
    key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography = tuple_result
    cubigma.prepare_machine(key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography)

    if mode == "encrypt":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(message, key_phrase)
        print(f"{encrypted_message=}")
    elif mode == "decrypt":
        encrypted_message = message
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(message, key_phrase)
        print(f"{decrypted_message=}")
    else:  # mode == "both":
        clear_text_message = message
        print(f"{clear_text_message=}")
        encrypted_message = cubigma.encrypt_message(clear_text_message, key_phrase)
        print(f"{encrypted_message=}")
        decrypted_message = cubigma.decrypt_message(encrypted_message, key_phrase)
        print(f"{decrypted_message=}")


if __name__ == "__main__":
    main()
