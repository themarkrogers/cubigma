"""
This file is used to encrypt and decrypt messages using the prepared cube.txt file.
This code implements the Cubigma encryption algorithm.
"""

from base64 import b64decode

from cubigma.core import get_hash_of_string_in_bytes, strengthen_key, DeterministicRandomCore
# from core import get_hash_of_string_in_bytes, strengthen_key, DeterministicRandomCore

from cubigma.utils import (  # Used in packaging & unit testing
# from utils import (  # Used in local debugging
    LENGTH_OF_TRIO,
    NOISE_SYMBOL,
    generate_cube_from_symbols,
    generate_plugboard,
    generate_reflector,
    generate_rotors,
    get_symbol_for_coordinates,
    get_encrypted_coordinates,
    parse_arguments,
    prep_string_for_encrypting,
    rotate_slice_of_cube,
    sanitize,
    split_to_human_readable_symbols,
    _user_perceived_length,
)


class Cubigma:
    """
    This class is used to encrypt and decrypt messages (with or without additional steganography)
    """

    _characters_filepath: str
    _cube_filepath: str
    _is_machine_prepared: bool = False
    _is_using_steganography: bool = False
    _num_trios_encoded = 0
    _symbols: list[str]
    plugboard: dict[str, str]
    reflector: dict[str, str]
    rotors: list[list[list[list[str]]]]
    random_core: DeterministicRandomCore | None

    def __init__(self, characters_filepath: str = "characters.txt", cube_filepath: str = "cube.txt"):
        self._characters_filepath = characters_filepath
        self._cube_filepath = cube_filepath
        self._is_machine_prepared = False
        self.plugboard = {}
        self.reflector = {}
        self.rotors = []
        self.random_core = None

    def _get_encrypted_letter_trio(self, char_trio: str, key_phrase: str, is_encrypting: bool) -> str:
        rev_rotors = list(reversed(self.rotors))
        step_one = self._run_trio_through_rotors(char_trio, self.rotors, key_phrase, is_encrypting)
        print(f"{step_one=}")
        step_two = self._run_trio_through_reflector(step_one, key_phrase, self._num_trios_encoded)
        print(f"{step_two=}")
        complete = self._run_trio_through_rotors(step_two, rev_rotors, key_phrase, is_encrypting)
        print(f"{complete=}")
        return complete

    def _run_message_through_plugboard(self, full_message: str) -> str:
        message_after_plugboard_ops = ""
        for symbol in full_message:
            corresponding_symbol = self.plugboard.get(symbol, symbol)  # Attempt to lookup, fail over to original symbol
            message_after_plugboard_ops += corresponding_symbol
        return message_after_plugboard_ops

    def _run_trio_through_reflector(
        self, char_trio: str, strengthened_key_phrase: str, num_of_encoded_trios: int
    ) -> str:
        """
        Reflects the trio deterministically using a hash-based reordering.

        Args:
            char_trio (str): The input trio of symbols.
            strengthened_key_phrase (str): A strengthened key phrase
            num_of_encoded_trios (int): This changes with each encoding, so that the same trio gets encoded
              differently each time

        Returns:
            str: The reflected trio.
        """
        reflected_symbols = []
        # Reflect each symbol
        for symbol in split_to_human_readable_symbols(char_trio):
            reflected_symbol = self.reflector[symbol]
            reflected_symbols.append(reflected_symbol)

        # Hash the trio to determine the reordering
        reflected_trio = "".join(reflected_symbols)
        hash_input = f"{reflected_trio}|{strengthened_key_phrase}|{num_of_encoded_trios}"
        trio_hash = get_hash_of_string_in_bytes(hash_input)

        # Determine the reordering using the first 3 bytes of the hash
        order = sorted(range(LENGTH_OF_TRIO), key=lambda i: trio_hash[i])

        # Reorder the trio based on the computed order
        reordered_reflected_trio = "".join(reflected_symbols[i] for i in order)

        return reordered_reflected_trio

    def _run_trio_through_rotors(
        self,
        char_trio: str,
        rotors: list[list[list[list[str]]]],
        key_phrase: str,
        is_encrypting: bool,
    ) -> str:
        cur_trio = char_trio
        for rotor_number, rotor in enumerate(rotors):
            print(f"{cur_trio=}")
            # Step the rotors forward immediately before encoding each trio on each rotor
            coordinate_by_char = {}
            stepped_rotor = self._step_rotor(rotor, rotor_number, key_phrase)
            rotors[rotor_number] = stepped_rotor

            individual_symbols = split_to_human_readable_symbols(cur_trio)
            for frame_idx, cur_frame in enumerate(stepped_rotor):
                for row_idx, cur_line in enumerate(cur_frame):
                    if any(symbol in cur_line for symbol in individual_symbols):
                        if individual_symbols[0] in cur_line:
                            point = (frame_idx, row_idx, cur_line.index(individual_symbols[0]))
                            coordinate_by_char[individual_symbols[0]] = point
                        if individual_symbols[1] in cur_line:
                            point = (frame_idx, row_idx, cur_line.index(individual_symbols[1]))
                            coordinate_by_char[individual_symbols[1]] = point
                        if individual_symbols[2] in cur_line:
                            point = (frame_idx, row_idx, cur_line.index(individual_symbols[2]))
                            coordinate_by_char[individual_symbols[2]] = point
            if len(coordinate_by_char) != LENGTH_OF_TRIO:
                print("This is unexpected")
            orig_indices = [coordinate_by_char[cur_char] for cur_char in individual_symbols]
            num_blocks = len(stepped_rotor)
            encrypted_coordinates = get_encrypted_coordinates(
                orig_indices[0],
                orig_indices[1],
                orig_indices[2],
                num_blocks,
                key_phrase,
                self._num_trios_encoded,
                is_encrypting,
            )
            if is_encrypting:
                self._num_trios_encoded += 1
            else:
                self._num_trios_encoded -= 1
            encrypted_char_1 = get_symbol_for_coordinates(encrypted_coordinates[0], stepped_rotor)
            encrypted_char_2 = get_symbol_for_coordinates(encrypted_coordinates[1], stepped_rotor)
            encrypted_char_3 = get_symbol_for_coordinates(encrypted_coordinates[2], stepped_rotor)
            list_of_encrypted_chars = [encrypted_char_1, encrypted_char_2, encrypted_char_3]
            encrypted_trio = "".join(list_of_encrypted_chars)
            cur_trio = encrypted_trio
            # ToDo: Do we need to save stepped_rotor back into
        return cur_trio

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
        combined_key = f"{strengthened_key_phrase}|{rotor_num}|{self._num_trios_encoded}"
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
        encrypted_message_after_plugboard = self._run_message_through_plugboard(encrypted_message)
        print(f"{encrypted_message_after_plugboard=}")
        raw_decrypted_message = self.encode_string(encrypted_message_after_plugboard, key_phrase, False)
        print(f"{raw_decrypted_message=}")
        decrypted_message = raw_decrypted_message.replace("", "").replace("", "").replace("", "")
        print(f"{decrypted_message=}")
        decrypted_message_after_plugboard = self._run_message_through_plugboard(decrypted_message)
        print(f"{decrypted_message_after_plugboard=}")
        return decrypted_message_after_plugboard

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

        # Remove all trios with the TOTAL_NOISE characters
        decrypted_message = ""
        message_split_into_symbols = split_to_human_readable_symbols(
            encrypted_message, expected_number_of_graphemes=None
        )
        for i in range(0, len(message_split_into_symbols), LENGTH_OF_TRIO):
            end_idx = i + LENGTH_OF_TRIO
            encrypted_chunk_symbols = message_split_into_symbols[i:end_idx]
            encrypted_chunk = "".join(encrypted_chunk_symbols)
            decrypted_chunk = self.decode_string(encrypted_chunk, key_phrase)
            if NOISE_SYMBOL not in decrypted_chunk:
                decrypted_message += decrypted_chunk
        print(f"{decrypted_message=}")
        return decrypted_message

    def encode_string(self, sanitized_message: str, key_phrase: str, is_encrypting: bool) -> str:
        """
        Encrypt the message using the playfair cube

        Args:
            sanitized_message (str): String prepared for encryption
            key_phrase (str): Secret key phrase
            is_encrypting (bool): A flag to help the direction of the encoding

        Returns:
            str: Encrypted string
        """
        if not self._is_machine_prepared:
            raise ValueError(
                "Machine is not prepared yet! Call .prepare_machine(key_phrase) before encoding or decoding"
            )
        assert _user_perceived_length(sanitized_message) % LENGTH_OF_TRIO == 0, "Message is not properly sanitized!"
        encrypted_message = ""
        message_split_into_symbols = split_to_human_readable_symbols(
            sanitized_message, expected_number_of_graphemes=None
        )
        for i in range(0, len(message_split_into_symbols), LENGTH_OF_TRIO):
            end_idx = i + LENGTH_OF_TRIO
            orig_chunk_symbols = message_split_into_symbols[i:end_idx]
            orig_chunk = "".join(orig_chunk_symbols)
            encrypted_chunk = self._get_encrypted_letter_trio(orig_chunk, key_phrase, is_encrypting)
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
        clear_text_message_after_plugboard = self._run_message_through_plugboard(clear_text_message)
        print(f"{clear_text_message_after_plugboard=}")
        sanitized_string = prep_string_for_encrypting(clear_text_message_after_plugboard)
        print(f"{sanitized_string=}")
        encrypted_message = self.encode_string(sanitized_string, key_phrase, True)
        encrypted_message_after_plugboard = self._run_message_through_plugboard(encrypted_message)
        print(f"{encrypted_message_after_plugboard=}")
        return encrypted_message_after_plugboard

    def prepare_machine(
        self,
        key_phrase: str,
        cube_length: int,
        num_rotors_to_make: int,
        rotors_to_use: list[int],
        should_use_steganography: bool,
        plugboard_values: list[str],
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
            plugboard_values: (list[str]), list of pairs of symbols to use as the plugboard (i.e. swap)
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
            # salt_bytes = b64decode("K6eqcp4HvxKAviVN+0NUDw==")
            salt_bytes = salt
        else:
            salt_bytes = b64decode(salt)
        strengthened_key_phrase, bases64_encoded_salt = strengthen_key(key_phrase, salt=salt_bytes)
        print(f"{strengthened_key_phrase=}")
        print(f"{bases64_encoded_salt=}")
        for character in split_to_human_readable_symbols(strengthened_key_phrase, expected_number_of_graphemes=44):
            if character not in self._symbols:
                raise ValueError("Key was strengthened to include an invalid character")

        # Setup random seeds
        self.random_core = DeterministicRandomCore(strengthened_key_phrase)

        # Set up the rotors and the reflector
        rotors = generate_rotors(
            strengthened_key_phrase,
            raw_cube,
            num_rotors_to_make=num_rotors_to_make,
            rotors_to_use=rotors_to_use,
            orig_key_length=len(key_phrase),
        )
        _ = [print(f"First char of rotor: {rotor[0][0][0]}") for rotor in rotors]
        reflector = generate_reflector(self._symbols, self.random_core)
        print(f"{reflector["A"]=}, {reflector["B"]=}, {reflector["C"]=}, {reflector["D"]=}")
        plugboard = generate_plugboard(plugboard_values)
        print(f"{plugboard=}")
        self.plugboard = plugboard
        self.reflector = reflector
        self.rotors = rotors
        self._is_using_steganography = should_use_steganography
        print(f"{should_use_steganography=}")
        self._is_machine_prepared = True
        return bases64_encoded_salt


def main() -> None:
    """
    Entrypoint for the cubigma project.

    Returns:
        None
    """
    cubigma = Cubigma("characters.txt", "cube.txt")

    tuple_result = parse_arguments()
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

    print(f"{mode=}")
    if mode == "encrypt":
        salt = cubigma.prepare_machine(
            key_phrase,
            cube_length,
            num_rotors_to_make,
            rotors_to_use,
            should_use_steganography,
            plugboard_values,
            salt=None,
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
            key_phrase,
            cube_length,
            num_rotors_to_make,
            rotors_to_use,
            should_use_steganography,
            plugboard_values,
            salt=salt,
        )
        decrypted_message = cubigma.decrypt_message(encrypted_message, key_phrase)
        print(f"{decrypted_message=}")
    else:
        raise ValueError("Unexpected mode!")
    print("Done!\n")


if __name__ == "__main__":
    main()
