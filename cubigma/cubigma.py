"""
This file is used to encrypt and decrypt messages using the prepared cube.txt file.
This code implements the Cubigma encryption algorithm.
"""

from base64 import b64decode

# from cubigma.utils import (  # Used in packaging & unit testing
from utils import (  # Used in local debugging
    LENGTH_OF_QUARTET,
    NOISE_SYMBOL,
    generate_cube_from_symbols,
    generate_rotors,
    get_chars_for_coordinates,
    get_opposite_corners,
    parse_arguments,
    prep_string_for_encrypting,
    rotate_slice_of_cube,
    run_quartet_through_reflector,
    sanitize,
    split_to_human_readable_symbols,
    strengthen_key,
)


class Cubigma:
    """
    This class is used to encrypt and decrypt messages (with or without additional steganography)
    """

    _characters_filepath: str
    _cube_filepath: str
    _is_machine_prepared: bool = False
    _is_using_steganography: bool = False
    _num_quartets_encoded = 0
    _symbols: list[str]
    rotors: list[list[list[list[str]]]]

    def __init__(self, characters_filepath: str = "characters.txt", cube_filepath: str = "cube.txt"):
        self._characters_filepath = characters_filepath
        self._cube_filepath = cube_filepath
        self._is_machine_prepared = False

    def _get_encrypted_letter_quartet(self, char_quartet: str, key_phrase: str) -> str:
        rev_rotors = list(reversed(self.rotors))
        step_one = self._run_quartet_through_rotors(char_quartet, self.rotors, key_phrase)
        step_two = run_quartet_through_reflector(step_one, key_phrase, self._num_quartets_encoded)
        complete = self._run_quartet_through_rotors(step_two, rev_rotors, key_phrase)
        return complete

    def _run_quartet_through_rotors(
        self, char_quartet: str, rotors: list[list[list[list[str]]]], key_phrase: str
    ) -> str:
        indices_by_char = {}
        cur_quartet = char_quartet
        for rotor_number, rotor in enumerate(rotors):
            # Step the rotors forward immediately before encoding each quartet on each rotor
            stepped_rotor = self._step_rotor(rotor, rotor_number, key_phrase)
            rotors[rotor_number] = stepped_rotor

            for frame_idx, cur_frame in enumerate(stepped_rotor):
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
            for cur_char in split_to_human_readable_symbols(cur_quartet):
                orig_indices.append(indices_by_char[cur_char])
            num_blocks = len(stepped_rotor)
            lines_per_block = len(stepped_rotor[0])
            symbols_per_line = len(stepped_rotor[0][0])
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
            encrypted_char_1 = get_chars_for_coordinates(encrypted_indices[0], stepped_rotor)
            encrypted_char_2 = get_chars_for_coordinates(encrypted_indices[1], stepped_rotor)
            encrypted_char_3 = get_chars_for_coordinates(encrypted_indices[2], stepped_rotor)
            encrypted_char_4 = get_chars_for_coordinates(encrypted_indices[3], stepped_rotor)
            encrypted_quartet = "".join([encrypted_char_1, encrypted_char_2, encrypted_char_3, encrypted_char_4])
            cur_quartet = encrypted_quartet
            # ToDo: Do we need to save stepped_rotor back into
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

        msg = f"The file must contain at least {total_num_of_symbols} symbols. Found {len(symbols)}"
        assert len(symbols) >= total_num_of_symbols, msg

        trimmed_symbols = symbols[0:total_num_of_symbols]

        # Reverse, so the least common symbols are first; this helps entropy when loading the key phrase
        readied_symbols = list(reversed(list(trimmed_symbols)))
        return readied_symbols

    def _step_rotor(
        self, rotor: list[list[list[str]]], rotor_num: int, strengthened_key_phrase: str
    ) -> list[list[list[str]]]:
        combined_key = f"{strengthened_key_phrase}|{rotor_num}|{self._num_quartets_encoded}"
        return rotate_slice_of_cube(rotor, combined_key)

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
            encrypted_message (str): Salt + Encrypted message
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
        salt: str | None = None,
    ) -> str:
        """
        This function must be called before encrypting or decrypting messages. This readies the machine for use.

        Args:
            key_phrase: (str), secret key phrase in its original form
            cube_length: (int), the length of one side of the playfair cube
            num_rotors_to_make: (int), number of rotors to generate
            rotors_to_use: (list[int]), which of the generated rotors to use
            should_use_steganography: (bool), encryption or encryption+steganography
            salt: (str | None), plain text salt. Only needed for decrypting

        Returns:
            (str): the plain text salt used to strengthen the key
        """
        # Set up user-configurable parameters (similar to configuring the plug board on an Enigma machine)
        self._symbols = self._read_characters_file(cube_length)
        raw_cube = generate_cube_from_symbols(
            self._symbols, num_blocks=cube_length, lines_per_block=cube_length, symbols_per_line=cube_length
        )

        salt_bytes: bytes | None
        if salt is None:
            salt_bytes = salt
        else:
            # salt_bytes = salt.encode("utf-8")
            salt_bytes = b64decode(salt)
        strengthened_key_phrase, bases64_encoded_salt = strengthen_key(key_phrase, salt=salt_bytes)
        for character in split_to_human_readable_symbols(strengthened_key_phrase, expected_number_of_graphemes=44):
            if character not in self._symbols:
                raise ValueError("Key was strengthened to include an invalid character")

        # Set up the rotors and the reflector
        rotors = generate_rotors(
            strengthened_key_phrase,
            raw_cube,
            num_rotors_to_make=num_rotors_to_make,
            rotors_to_use=rotors_to_use,
            orig_key_length=len(key_phrase),
        )
        self.rotors = rotors
        self._is_using_steganography = should_use_steganography
        self._is_machine_prepared = True
        return bases64_encoded_salt


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
    # Encrypting: The salt is always 16-bytes long, and always prepended to the encrypted message
    # Steganography: Account for an extra 16-bits when calculating the sum_of_squares

    tuple_result = parse_arguments()
    key_phrase, mode, message, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography = tuple_result

    if mode == "encrypt":
        salt = cubigma.prepare_machine(
            key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography, salt=None
        )
        clear_text_message = message
        print(f"{clear_text_message=}")
        raw_encrypted_message = cubigma.encrypt_message(message, key_phrase)
        encrypted_message = salt + raw_encrypted_message  # ToDo: Fix this
        # ToDo Now: Need to print '\x06' as 1 character, not 4
        print(f"{encrypted_message=}")
    elif mode == "decrypt":
        encrypted_content = message
        # ToDo Now: Need to read '\x06' as 1 character, not 4
        print(f"{encrypted_content=}")
        length_of_salt = 24
        salt = message[0:length_of_salt]
        encrypted_message = message[length_of_salt:]
        print(f"{encrypted_message=}")
        cubigma.prepare_machine(
            key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography, salt=salt
        )
        decrypted_message = cubigma.decrypt_message(encrypted_message, key_phrase)
        print(f"{decrypted_message=}")
    else:
        raise ValueError("Unexpected mode!")


if __name__ == "__main__":
    main()
