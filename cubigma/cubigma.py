"""
This file is used to encrypt and decrypt messages using the prepared cuboid.txt file.
This is Step 2 (the main step) in The Cubigma encryption algorithm.
"""

import argparse
import random

from utils import read_config, user_perceived_length, LENGTH_OF_QUARTET, NOISE_SYMBOL

config = read_config()
SYMBOLS_PER_LINE = config["SYMBOLS_PER_LINE"]
LINES_PER_BLOCK = config["LINES_PER_BLOCK"]
NUM_BLOCKS = config["NUM_BLOCKS"]


# ToDo: This increases the complexity derived from the key
#   * Maybe: Rotate the slices in a manner based on the key
#   * Maybe: Change which corner of the cuboid is chosen
#   * Maybe: both?
# Split the key phrase into rough thirds. Come up with a logic that converts the string into an algorithm for rotation.
# Three parts of the key phrase, three axes of rotation. So, we need an algorithm that Takes the key third and the text
# being encoded/decoded and deterministically chooses which "slice" of the prism to rotate, and which way.
# Maybe: Combine these three elements: The sum of ord() of the key phrase, of the decoded string, and of the encoded
# quartet. This will yield the same three numbers both encoding/decoding (e.g. val = (clear ^ key) - encrypted). With
# this number, we determine which slice (e.g. val % key third % SIZE_OF_AXIS). We always turn it the same way (e.g.
# val % key third % 2). As long as we encode and decode in the same order, we'll be modifying the same starting cuboid
# in the same ways, allowing us to always get the correct opposite corners for decoding.

# ToDo: See if there is a way to make the cipher ever encode a letter as itself (a weakness in the enigma machine)


def _get_opposite_corners(
    point_one: tuple[int, int, int],
    point_two: tuple[int, int, int],
    point_three: tuple[int, int, int],
    point_four: tuple[int, int, int],
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """
    Given four corners of a rectangular cuboid, find the other four corners.

    Args:
        point_one: A tuple representing the first point (x, y, z).
        point_two: A tuple representing the second point (x, y, z).
        point_three: A tuple representing the third point (x, y, z).
        point_four: A tuple representing the fourth point (x, y, z).

    Returns:
        A tuple of four tuples, each representing the coordinates of the remaining corners.
    """
    # Check for unique points
    points = {point_one, point_two, point_three, point_four}
    if len(points) != LENGTH_OF_QUARTET:
        raise ValueError("The provided points must be unique and represent adjacent corners of a rectangular cuboid.")

    x1, y1, z1 = point_one
    x2, y2, z2 = point_two
    x3, y3, z3 = point_three
    x4, y4, z4 = point_four

    max_frame_idx = NUM_BLOCKS - 1
    max_row_idx = LINES_PER_BLOCK - 1
    max_col_idx = SYMBOLS_PER_LINE - 1

    point_five = (max_frame_idx - x1, max_row_idx - y1, max_col_idx - z1)
    point_six = (max_frame_idx - x2, max_row_idx - y2, max_col_idx - z2)
    point_seven = (max_frame_idx - x3, max_row_idx - y3, max_col_idx - z3)
    point_eight = (max_frame_idx - x4, max_row_idx - y4, max_col_idx - z4)

    return point_five, point_six, point_seven, point_eight


def _get_prefix_order_number_quartet(order_number: int) -> str:
    order_number_str = str(order_number)
    assert len(order_number_str) == 1, "Invalid order number"
    pad_symbols = ["", "", "", order_number_str]
    random.shuffle(pad_symbols)
    return "".join(pad_symbols)


def _pad_chunk_with_rand_pad_symbols(chunk: str) -> str:
    pad_symbols = ["", "", ""]
    max_pad_idx = len(pad_symbols) - 1
    while len(chunk) < LENGTH_OF_QUARTET:
        new_random_number = random.randint(0, max_pad_idx)
        random_pad_symbol = pad_symbols[new_random_number]
        if random_pad_symbol not in chunk:
            chunk += random_pad_symbol
    return chunk


def _remove_duplicate_letters(orig: str) -> str:
    unique_letters = []
    for letter in orig:
        if letter not in unique_letters:
            unique_letters.append(letter)
    return "".join(list(unique_letters))


def prep_string_for_encrypting(orig_message: str) -> str:
    """
    Pad the string with random pad symbols until its length is a multiple of 4

    Args:
        orig_message (str): String to be prepared for encryption

    Returns:
        str: String prepared for encryption
    """
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
    sanitized_string += cur_chunk
    return sanitized_string


class Cubigma:
    cuboid_filepath: str
    playfair_cuboid: list[list[list[str]]]

    def __init__(self, cuboid_filepath: str):
        self.cuboid_filepath = cuboid_filepath

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

    def _promote_letter(self, symbol_to_promote: str) -> None:
        """
        Promote a given symbol within a 3D array of characters (playfair_cuboid) by removing it from its
        current position and pushing it to the first position in the first row, while cascading other
        elements down to fill the resulting gaps.

        Args:
            symbol_to_promote (str): The ASCII character to promote to the top-left.

        Returns:
            None
        """
        assert self.playfair_cuboid, "Playfair cuboid not prepared yet!"
        # Find the location of the symbol_to_promote
        found = False
        frame_index = -1
        row_index = -1
        for frame_index, frame in enumerate(self.cuboid_filepath):
            for row_index, row in enumerate(frame):
                if symbol_to_promote in row:
                    col_index = row.index(symbol_to_promote)
                    row.pop(col_index)  # Remove the symbol from its current position
                    frame[row_index] = row
                    self.cuboid_filepath[frame_index] = frame
                    found = True
                    break
            if found:
                break

        if not found:
            raise ValueError(f"Symbol '{symbol_to_promote}' not found in playfair_cuboid.")

        # Cascade the "hole" to the front
        char_to_move = ""
        did_finish_moving_chars = False
        for frame_idx in range(0, NUM_BLOCKS):
            cur_frame = self.cuboid_filepath[frame_idx]
            for row_idx in range(0, LINES_PER_BLOCK):
                cur_row = cur_frame[row_idx]
                if frame_idx == frame_index and row_idx == row_index:
                    # Add the char onto this row
                    if char_to_move:
                        new_row = [char_to_move] + cur_row
                    else:
                        new_row = cur_row
                    new_frame = cur_frame
                    new_frame[row_idx] = new_row
                    self.cuboid_filepath[frame_idx] = new_frame
                    did_finish_moving_chars = True
                    break
                # Push the chars off the end of this row
                if char_to_move:
                    new_row = [char_to_move] + cur_row[0:-1]
                else:
                    new_row = cur_row[0:-1]
                char_to_move = cur_row[-1]
                new_frame = cur_frame
                new_frame[row_idx] = new_row
                self.cuboid_filepath[frame_idx] = new_frame
            if did_finish_moving_chars:
                break

        # Add symbol to front
        first_frame = self.cuboid_filepath[0]
        first_row = first_frame[0]
        new_first_row = [symbol_to_promote] + first_row
        new_first_frame = first_frame
        new_first_frame[0] = new_first_row
        self.cuboid_filepath[0] = new_first_frame

    def prepare_cuboid_with_key_phrase(self, key_phrase: str) -> None:
        """
        Read the cuboid from disk and reorder it according to the key phrase provided

        Args:
            key_phrase (str): Key phrase to use for encrypting/decrypting

        Returns:
            None
        """
        assert len(key_phrase) >= 3, "Key phrase must be at least 3 characters long"
        self._read_cuboid_from_disk()
        sanitized_key_phrase = _remove_duplicate_letters(key_phrase)
        reversed_key = list(reversed(sanitized_key_phrase))
        for key_letter in reversed_key:
            self._promote_letter(key_letter)

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
        encrypted_indices = _get_opposite_corners(orig_indices[0], orig_indices[1], orig_indices[2], orig_indices[3])
        encrypted_char_one = self._get_chars_for_coordinates(encrypted_indices[0])
        encrypted_char_two = self._get_chars_for_coordinates(encrypted_indices[1])
        encrypted_char_three = self._get_chars_for_coordinates(encrypted_indices[2])
        encrypted_char_four = self._get_chars_for_coordinates(encrypted_indices[3])
        encrypted_quartet = "".join([encrypted_char_one, encrypted_char_two, encrypted_char_three, encrypted_char_four])
        return encrypted_quartet

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
                padded_chunk = _pad_chunk_with_rand_pad_symbols(padded_chunk)
            random_noise_chunk = self._get_random_noise_chunk()
            padded_chunk += random_noise_chunk
        prefix_order_number_quartet = _get_prefix_order_number_quartet(chunk_order_number)
        result = prefix_order_number_quartet + padded_chunk
        return result

    def encrypt_message(self, key_phrase: str, clear_text_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            key_phrase (str): Key phrase used to encrypt the message
            clear_text_message (str): Message to encrypt

        Returns:
            str: Encrypted string
        """
        self.prepare_cuboid_with_key_phrase(key_phrase)
        sanitized_string = prep_string_for_encrypting(clear_text_message)
        encrypted_message = self.encode_string(sanitized_string)
        return encrypted_message

    def decrypt_message(self, key_phrase: str, encrypted_message: str) -> str:
        """
        Decrypt the message using the playfair cuboid

        Args:
            key_phrase (str): Key phrase used to decrypt the message
            encrypted_message (str): Encrypted message

        Returns:
            str: Decrypted string
        """
        self.prepare_cuboid_with_key_phrase(key_phrase)

        # Remove all quartets with the TOTAL_NOISE characters
        decrypted_message = ""
        for i in range(0, len(encrypted_message), LENGTH_OF_QUARTET):
            end_idx = i + LENGTH_OF_QUARTET
            encrypted_chunk = encrypted_message[i:end_idx]
            decrypted_chunk = self.decode_string(encrypted_chunk)
            if NOISE_SYMBOL not in decrypted_chunk:
                decrypted_message += decrypted_chunk
        return decrypted_message


def _parse_arguments() -> tuple[str, str, str]:
    """
    Parses runtime arguments or prompts the user for input interactively.

    Returns:
        tuple[str, str, str]: A tuple containing key_phrase, mode ('encrypt' or 'decrypt'), and the message.
    """
    parser = argparse.ArgumentParser(description="Encrypt or decrypt a message using a key phrase.")
    parser.add_argument("key_phrase", type=str, help="The key phrase for encryption/decryption.")
    parser.add_argument("--clear_text_message", type=str, help="The plaintext message to encrypt.")
    parser.add_argument("--encrypted_message", type=str, help="The encrypted message to decrypt.")

    args = parser.parse_args()

    if not args.clear_text_message and not args.encrypted_message:
        print("No runtime arguments provided. Switching to interactive mode.")
        mode = input("Are you encrypting or decrypting? (encrypt/decrypt/both): ").strip().lower()
        while mode not in {"encrypt", "decrypt", "both"}:
            mode = input("Invalid choice. Please enter 'encrypt', 'decrypt', or 'both': ").strip().lower()

        key_phrase = input("Enter your key phrase: ").strip()
        if mode in ("encrypt" , "both"):
            message = input("Enter your plaintext message: ").strip()
        else:
            message = input("Enter your encrypted message: ").strip()

        return key_phrase, mode, message

    if args.clear_text_message and args.encrypted_message:
        parser.error("Provide only one of --clear_text_message or --encrypted_message, not both.")

    key_phrase = args.key_phrase
    if args.clear_text_message:
        return key_phrase, "encrypt", args.clear_text_message
    return key_phrase, "decrypt", args.encrypted_message


def main() -> None:
    """
    Entrypoint for the cubigma project.

    Returns:
        None
    """
    key_phrase, mode, message = _parse_arguments()
    # key_phrase = "Rumpelstiltskin"
    # clear_text_message = "This is cool!"
    cubigma = Cubigma("cuboid.txt")
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
