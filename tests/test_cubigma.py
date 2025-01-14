# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, mock_open, MagicMock
import os
import unittest

from cubigma.cubigma import NOISE_SYMBOL, Cubigma, main


# Testing Private Cubigma Functions


class TestGetEncryptedLetterQuartet(unittest.TestCase):

    def test_get_encrypted_letter_quartet(self):
        # Arrange
        cubigma = Cubigma()
        expected_rotors = [
            [[["a", "b"], ["c", "d"]], [["e", "f"], ["g", "h"]]],
            [[["e", "f"], ["g", "h"]], [["a", "b"], ["c", "d"]]],
            [[["h", "g"], ["f", "e"]], [["d", "c"], ["b", "a"]]],
        ]
        cubigma.rotors = expected_rotors
        test_char_quartet = "fade"
        expected_str_1 = "cafe"
        expected_result = "bead"
        expected_middle_str = "head"
        mock_run_quartet_through_rotors = MagicMock()
        mock_run_quartet_through_rotors.side_effect = [expected_str_1, expected_result]
        cubigma._run_quartet_through_rotors = mock_run_quartet_through_rotors  # pylint:disable=W0212
        mock_run_quartet_through_reflector = MagicMock()
        mock_run_quartet_through_reflector.return_value = expected_middle_str
        cubigma._run_quartet_through_reflector = mock_run_quartet_through_reflector  # pylint:disable=W0212
        test_key_phrase = "foo"

        # Act
        result = cubigma._get_encrypted_letter_quartet(test_char_quartet, test_key_phrase)  # pylint:disable=W0212

        # Assert
        self.assertEqual(expected_result, result)
        mock_run_quartet_through_reflector.assert_called_once_with(expected_str_1)


class TestReadCharactersFile(unittest.TestCase):
    def setUp(self):
        self.cube_length = 4
        self.symbols = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            ",",
            ".",
            "?",
            "!",
            "-",
            "_",
        ]

    @patch("builtins.open")
    def test_valid_file(self, mock_open_func):
        # Arrange
        mock_data_array = [
            self.symbols[i * self.cube_length * self.cube_length + j * self.cube_length + k]
            for i in range(self.cube_length)
            for j in range(self.cube_length)
            for k in range(self.cube_length)
        ]
        mock_data = "\n".join(mock_data_array)
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212

        # Assert
        expected_symbols = list(reversed(mock_data_array))
        self.assertEqual(result, expected_symbols)

    @patch("builtins.print")
    @patch("builtins.open")
    def test_invalid_file_symbol_length(self, mock_open_func, mock_print):
        # Arrange
        mock_data = "\n".join(self.symbols[i] for i in range(len(self.symbols)))
        mock_data = mock_data.replace("a", "a\nA")
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value
        cubigma = Cubigma("characters.txt", "")

        # Act & Assert
        with self.assertRaises(AssertionError):
            cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212
        mock_print.assert_called_once_with("Duplicate symbol found: A")

    @patch("builtins.open")
    def test_missing_file(self, mock_open_func):
        # Arrange
        mock_open_func.side_effect = FileNotFoundError

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            cubigma = Cubigma("missing.txt", "")
            cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212

    @patch("builtins.open")
    def test_insufficient_symbols(self, mock_open_func):
        # Arrange
        test_cube_length = 10
        mock_data = "\n".join(self.symbols[i] for i in range(len(self.symbols)))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            cubigma = Cubigma("characters.txt", "")
            cubigma._read_characters_file(test_cube_length)  # pylint:disable=W0212
        self.assertIn("Not enough symbols are prepared", str(context.exception))

    @patch("builtins.print")
    @patch("builtins.open")
    def test_duplicate_symbols(self, mock_open_func, mock_print):
        # Arrange
        num_of_symbols = self.cube_length * self.cube_length * self.cube_length
        mock_data_array = [
            self.symbols[i * self.cube_length * self.cube_length + j * self.cube_length + k]
            for i in range(self.cube_length)
            for j in range(self.cube_length)
            for k in range(self.cube_length)
        ]
        mock_data_array.pop(len(mock_data_array) - 1)
        mock_data_array.insert(0, "a")
        mock_data = "\n".join(mock_data_array)
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act & Assert
        # with patch("builtins.print") as mock_print:
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212
        assert len(result) == num_of_symbols
        mock_print.assert_called_once()

    @patch("builtins.open")
    def test_exact_symbols_with_empty_lines(self, mock_open_func):
        # Arrange
        mock_data_array = [
            self.symbols[i * self.cube_length * self.cube_length + j * self.cube_length + k]
            for i in range(self.cube_length)
            for j in range(self.cube_length)
            for k in range(self.cube_length)
        ]
        mock_data = "\n".join(mock_data_array + ["" for _ in range(5)])
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212

        # Assert
        expected_symbols = list(reversed(mock_data_array))
        self.assertEqual(result, expected_symbols)


class TestReadCubeFromDisk(unittest.TestCase):

    def setUp(self):
        self.cube_file_path = "mock_cube_file.txt"
        self.cube_length = 3  # Example cube length

    def mock_user_perceived_length(self, line):
        """Mock function for user_perceived_length."""
        return len(line)

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length")
    def test_valid_cube(self, mock_length, mock_open_file):
        # Mock file content (valid 3x3x3 cube)
        mock_file_content = ["abc\n", "def\n", "ghi\n", "\n", "jkl", "mno", "pqr", "\n", "stu", "vwx", "yz "]
        mock_lengths = [3] * 9
        mock_open_file.return_value.readlines.return_value = mock_file_content
        mock_length.side_effect = mock_lengths

        # Expected cube structure
        expected_cube = [
            [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]],
            [["j", "k", "l"], ["m", "n", "o"], ["p", "q", "r"]],
            [["s", "t", "u"], ["v", "w", "x"], ["y", "z", " "]],
        ]

        # Create an instance of the class and call the method
        obj = Cubigma(self.cube_file_path)
        result = obj._read_cube_from_disk(self.cube_length)  # pylint:disable=W0212

        self.assertEqual(result, expected_cube)

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length")
    def test_invalid_line_length(self, mock_length, mock_open_file):
        # Mock file content with an invalid line length
        mock_file_content = (
            "abcdefg\n"  # Invalid line (length > 6)
            "\n"
        )
        mock_open_file.return_value.readlines.return_value = mock_file_content
        mock_length.return_value = 7

        obj = Cubigma(self.cube_file_path)

        with self.assertRaises(ValueError) as context:
            obj._read_cube_from_disk(self.cube_length)  # pylint:disable=W0212

        self.assertIn("unexpected", str(context.exception))

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length", side_effect=mock_user_perceived_length)
    def test_empty_file(self, mock_length, mock_open_file):
        # Arrange
        mock_file_content = ""
        mock_open_file.return_value.readlines.return_value = mock_file_content
        cubigma = Cubigma(self.cube_file_path)

        # Act
        result = cubigma._read_cube_from_disk(self.cube_length)  # pylint:disable=W0212

        # Assert
        self.assertEqual(result, [])
        mock_length.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length", side_effect=mock_user_perceived_length)
    def test_incomplete_frame(self, mock_length, mock_open_file):
        # Arrange
        mock_file_content = "abc\ndef\n"  # Only 2 lines, 1 line short of a complete frame
        mock_open_file.return_value.read.return_value = mock_file_content
        obj = Cubigma(self.cube_file_path)

        # Act
        result = obj._read_cube_from_disk(self.cube_length)  # pylint:disable=W0212

        # Assert
        self.assertEqual(result, [])
        mock_length.assert_not_called()


class TestRunQuartetThroughReflector(unittest.TestCase):

    @patch("cubigma.cubigma.index_to_quartet")
    @patch("cubigma.cubigma.quartet_to_index")
    def test_run_quartet_through_reflector_valid(self, mock_quartet_to_index, mock_index_to_quartet):
        # Arrange
        cubigma = Cubigma()
        cubigma._is_machine_prepared = True  # pylint:disable=W0212
        expected_symbols = ["A", "B", "C"]
        cubigma._symbols = expected_symbols  # pylint:disable=W0212
        expected_quartet_index = 42
        expected_reflected_index = 9001
        mock_reflector = {expected_quartet_index: expected_reflected_index}
        cubigma.reflector = mock_reflector

        mock_quartet_to_index.return_value = expected_quartet_index
        expected_result = "456"
        mock_index_to_quartet.return_value = expected_result
        test_char_quartet = "123"

        # Act
        result = cubigma._run_quartet_through_reflector(test_char_quartet)  # pylint:disable=W0212

        # Assert
        self.assertEqual(expected_result, result)
        mock_quartet_to_index.assert_called_once_with(test_char_quartet, expected_symbols)
        mock_index_to_quartet.assert_called_once_with(expected_reflected_index, expected_symbols)

    def test_run_quartet_through_reflector_invalid(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma._run_quartet_through_reflector("foo")  # pylint:disable=W0212


class TestRunQuartetThroughRotors(unittest.TestCase):

    @patch("cubigma.cubigma.get_opposite_corners")
    @patch("cubigma.cubigma.get_chars_for_coordinates")
    def test_basic_case(self, mock_get_chars, mock_get_corners):
        # Arrange
        cubigma_instance = Cubigma()
        mock_chars_data = ["W", "X", "Y", "Z", "E", "F", "G", "H", "I", "J", "K", "L"]
        mock_get_chars.side_effect = mock_chars_data
        mock_get_corners.side_effect = [[6, 2, 7, 0], [0, 1, 2, 3], [4, 5, 6, 7]]
        expected_result = "".join(mock_chars_data[-4:])
        char_quartet = "ABCD"
        rotors = [
            [
                [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
                [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
                [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
            ],
            [
                [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
                [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
                [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
            ],
            [
                [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
                [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
                [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
            ],
        ]
        key_phrase = "testkey"

        # Act
        result = cubigma_instance._run_quartet_through_rotors(char_quartet, rotors, key_phrase)  # pylint:disable=W0212

        # Assert
        self.assertEqual(result, expected_result)
        assert mock_get_chars.call_count == 4 * len(rotors)
        assert mock_get_corners.call_count == len(rotors)

    @patch("cubigma.cubigma.get_opposite_corners")
    @patch("cubigma.cubigma.get_chars_for_coordinates")
    def test_no_matching_characters(self, mock_get_chars, mock_get_corners):
        # Arrange
        cubigma_instance = Cubigma()
        char_quartet = "wxyz"
        rotors = [
            [
                [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
                [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
                [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
            ]
        ]
        key_phrase = "testkey"

        # Act & Assert
        with self.assertRaises(KeyError):
            cubigma_instance._run_quartet_through_rotors(char_quartet, rotors, key_phrase)  # pylint:disable=W0212
        mock_get_chars.assert_not_called()
        mock_get_corners.assert_not_called()

    @patch("cubigma.cubigma.get_opposite_corners")
    @patch("cubigma.cubigma.get_chars_for_coordinates")
    def test_valid_case_with_single_rotor(self, mock_get_chars, mock_get_corners):
        # Arrange
        cubigma_instance = Cubigma()
        mock_chars_data = ["W", "X", "Y", "Z", "E", "F", "G", "H", "I", "J", "K", "L"]
        mock_get_chars.side_effect = mock_chars_data
        mock_get_corners.side_effect = [[6, 2, 7, 0], [0, 1, 2, 3], [4, 5, 6, 7]]
        expected_result = "".join(mock_chars_data[:4])
        char_quartet = "ABCD"
        rotors = [
            [
                [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]],
                [["J", "K", "L"], ["M", "N", "O"], ["P", "Q", "R"]],
                [["S", "T", "U"], ["V", "W", "X"], ["Y", "Z", "0"]],
            ]
        ]
        expected_coord_for_a = (0, 0, 2)
        expected_coord_for_b = (0, 1, 2)
        expected_coord_for_c = (0, 2, 2)
        expected_coord_for_d = (0, 0, 1)
        key_phrase = "testkey"

        # Act
        result = cubigma_instance._run_quartet_through_rotors(char_quartet, rotors, key_phrase)  # pylint:disable=W0212

        # Assert
        self.assertEqual(result, expected_result)
        assert mock_get_chars.call_count == 4
        mock_get_corners.assert_called_once_with(
            expected_coord_for_a,
            expected_coord_for_b,
            expected_coord_for_c,
            expected_coord_for_d,
            len(rotors[0]),
            len(rotors[0][0]),
            len(rotors[0][0][0]),
            key_phrase,
            0,
        )


class TestWriteCubeFile(unittest.TestCase):
    def setUp(self):
        """Set up the test case."""
        self.test_filepath = "test_cube_output.txt"

    def tearDown(self):
        """Clean up the test case."""
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)

    def test_write_cube_file(self):
        """Test the _write_cube_file method."""
        symbols = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 5
        cubigma = Cubigma()
        cubigma._cube_filepath = self.test_filepath  # pylint:disable=W0212

        cubigma._write_cube_file(  # pylint:disable=W0212
            symbols=symbols,
            num_blocks=num_blocks,
            lines_per_block=lines_per_block,
            symbols_per_line=symbols_per_line,
        )

        # Verify the output file
        with open(self.test_filepath, "r", encoding="utf-8") as file:
            content = file.read()

        expected_content = """ABCDE\nFGHIJ\n\nKLMNO\nPQRST\n"""
        self.assertEqual(content, expected_content)

    @patch("cubigma.cubigma.user_perceived_length")
    def test_write_cube_file_invalid_symbols_per_line(self, mock_length):
        """Test the _write_cube_file method with invalid symbols_per_line."""
        symbols = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        num_blocks = 2
        lines_per_block = 2
        symbols_per_line = 4  # Mismatch with user_perceived_length
        cubigma = Cubigma()
        cubigma._cube_filepath = self.test_filepath  # pylint:disable=W0212
        mock_length.return_value = 128

        with self.assertRaises(ValueError):
            cubigma._write_cube_file(  # pylint:disable=W0212
                symbols=symbols,
                num_blocks=num_blocks,
                lines_per_block=lines_per_block,
                symbols_per_line=symbols_per_line,
            )


# Testing Public Cubigma Functions


class TestDecodeString(unittest.TestCase):

    def test_decode_string_before_machine_prepared(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma.decode_string("foo", "bar")

    def test_decode_string_valid(self):
        # Arrange
        expected_return_value = "boop"
        cubigma = Cubigma()
        cubigma._is_machine_prepared = True  # pylint:disable=W0212
        mock_encode_string = MagicMock()
        mock_encode_string.return_value = "boop"
        cubigma.encode_string = mock_encode_string

        # Act
        result = cubigma.decode_string("foo", "bar")

        # Assert
        self.assertEqual(expected_return_value, result, "return value is not the expected value")
        mock_encode_string.assert_called_once_with("foo", "bar")


class TestDecryptMessage(unittest.TestCase):

    def test_decrypt_message_not_prepared(self):
        """
        Test decrypt_message with valid inputs and a prepared machine.
        """
        key_phrase = "testkey"
        encrypted_message_valid = "ENCR" + "YPTE" + "DSTR" + "INGS"

        cubigma = Cubigma()

        with self.assertRaises(ValueError):
            cubigma.decrypt_message(encrypted_message_valid, key_phrase)

    def test_decrypt_message_valid_without_noise(self):
        """
        Test decrypt_message with valid inputs and a prepared machine.
        """
        key_phrase = "testkey"
        encrypted_message_valid = "ENCR" + "YPTE" + "DSTR" + "INGS"
        mock_data = ["DECR", "YPTE", "DSTR", "INGS"]
        expected_output = "".join(mock_data)

        cubigma = Cubigma()
        cubigma._is_machine_prepared = True  # pylint:disable=W0212
        mock_decode = MagicMock()
        mock_decode.side_effect = mock_data
        cubigma.decode_string = mock_decode

        result = cubigma.decrypt_message(encrypted_message_valid, key_phrase)

        self.assertEqual(expected_output, result)
        assert mock_decode.call_count == 4

    def test_decrypt_message_valid_with_noise(self):
        """
        Test decrypt_message with valid inputs and a prepared machine.
        """
        key_phrase = "testkey"
        encrypted_message_valid = (
            "ENCR"
            + f"1{NOISE_SYMBOL}34"
            + "YPTE"
            + f"12{NOISE_SYMBOL}4"
            + "DSTR"
            + f"123{NOISE_SYMBOL}"
            + "INGS"
            + f"{NOISE_SYMBOL}234"
        )
        mock_data = ["DECR", "foo1", "YPTE", "foo2", "DSTR", "foo3", "INGS", "foo4"]
        expected_output = "".join(mock_data)

        cubigma = Cubigma()
        cubigma._is_machine_prepared = True  # pylint:disable=W0212
        mock_decode = MagicMock()
        mock_decode.side_effect = mock_data
        cubigma.decode_string = mock_decode

        result = cubigma.decrypt_message(encrypted_message_valid, key_phrase)

        self.assertEqual(expected_output, result)
        assert mock_decode.call_count == 8


class TestEncodeMessage(unittest.TestCase):

    def test_encode_string_machine_not_prepared(self):
        """Test encode_string raises ValueError when machine is not prepared."""
        # This case is already covered, but we'll keep it for completeness.
        sanitized_message = "ABCDEFGH"
        key_phrase = "SECRET"
        instance = Cubigma()  # Not prepared yet

        with self.assertRaises(ValueError):
            instance.encode_string(sanitized_message, key_phrase)

    def test_encode_string_valid(self):
        """Test encode_string with valid inputs."""
        # Arrange
        sanitized_message = "ABCDEFGH"  # Example sanitized message
        key_phrase = "SECRET"
        instance = Cubigma()
        instance._is_machine_prepared = True  # pylint:disable=W0212
        mock_data = ["STUV", "WXYZ"]
        mock_get_encrypted_letter_quartet = MagicMock()
        mock_get_encrypted_letter_quartet.side_effect = mock_data
        instance._get_encrypted_letter_quartet = mock_get_encrypted_letter_quartet  # pylint:disable=W0212
        expected_result = "".join(mock_data)

        # Act
        result = instance.encode_string(sanitized_message, key_phrase)

        # Assert
        self.assertIsInstance(result, str)
        self.assertEqual(expected_result, result)
        assert mock_get_encrypted_letter_quartet.call_count == 2

    def test_encode_string_invalid_sanitized_message(self):
        """Test encode_string raises AssertionError for invalid sanitized message length."""
        # Arrange
        sanitized_message = "ABCDE"  # Invalid length (not divisible by LENGTH_OF_QUARTET)
        key_phrase = "SECRET"
        instance = Cubigma()
        instance._is_machine_prepared = True  # pylint:disable=W0212

        # Act & Assert
        with self.assertRaises(AssertionError):
            instance.encode_string(sanitized_message, key_phrase)


class TestEncryptMessage(unittest.TestCase):

    def test_encrypt_message_before_machine_prepared(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma.encrypt_message("foo", "bar")

    @patch("cubigma.cubigma.prep_string_for_encrypting")
    def test_encrypt_message_valid(self, mock_prep_string_for_encrypting):
        # Arrange
        expected_return_value = "boop"
        cubigma = Cubigma()
        cubigma._is_machine_prepared = True  # pylint:disable=W0212
        expected_string = "bar"
        mock_prep_string_for_encrypting.return_value = expected_string
        mock_encode_string = MagicMock()
        mock_encode_string.return_value = expected_return_value
        cubigma.encode_string = mock_encode_string

        # Act
        result = cubigma.encrypt_message("foo", "baz")

        # Assert
        self.assertEqual(expected_return_value, result, "return value is not the expected value")
        mock_encode_string.assert_called_once_with(expected_string, "baz")


class TestCubigma(unittest.TestCase):

    def configure(self, mock_strengthen_key, mock_split, mock_generate_rotors):
        cubigma = Cubigma()
        mock_read_characters_file = MagicMock()
        mock_symbols = ["a", "b"]
        mock_read_characters_file.return_value = mock_symbols
        cubigma._read_characters_file = mock_read_characters_file  # pylint:disable=W0212
        mock_write_cube_file = MagicMock()
        cubigma._write_cube_file = mock_write_cube_file  # pylint:disable=W0212
        mock_read_cube_from_disk = MagicMock()
        mock_cube = ["A", "C"]
        mock_read_cube_from_disk.return_value = mock_cube
        cubigma._read_cube_from_disk = mock_read_cube_from_disk  # pylint:disable=W0212
        mock_encoded_strengthened_key = "1"
        expected_salt = "2"
        mock_strengthen_key.return_value = mock_encoded_strengthened_key, expected_salt
        test_char_in_symbols = mock_symbols[0]
        mock_split.return_value = test_char_in_symbols
        mock_rotors = [1, 2, 3, 4]
        mock_generate_rotors.return_value = mock_rotors
        expected_num_unique_quartets = 17550
        key_phrase = "validKey123"
        cube_length = 3
        num_rotors_to_make = 3
        rotors_to_use = [2, 0]
        should_use_steganography = True
        return (
            cubigma,
            expected_num_unique_quartets,
            key_phrase,
            cube_length,
            num_rotors_to_make,
            rotors_to_use,
            should_use_steganography,
            expected_salt,
            mock_read_characters_file,
            mock_write_cube_file,
            mock_symbols,
            mock_read_cube_from_disk,
            mock_encoded_strengthened_key,
            mock_cube,
        )

    def validate(
        self,
        cubigma,
        should_use_steganography,
        expected_salt,
        result_salt,
        mock_read_characters_file,
        mock_write_cube_file,
        cube_length,
        mock_symbols,
        mock_read_cube_from_disk,
        mock_split,
        mock_encoded_strengthened_key,
        mock_generate_rotors,
        mock_cube,
        num_rotors_to_make,
        rotors_to_use,
        mock_read_reflector,
        expected_num_unique_quartets,
        key_phrase,
    ):
        self.assertTrue(cubigma._is_machine_prepared)  # pylint:disable=W0212
        self.assertTrue(cubigma._is_using_steganography)  # pylint:disable=W0212
        self.assertEqual(cubigma._is_using_steganography, should_use_steganography)  # pylint:disable=W0212
        self.assertEqual(expected_salt, result_salt)
        mock_read_characters_file.assert_called_once_with(cube_length)
        mock_write_cube_file.assert_called_once_with(
            mock_symbols, num_blocks=cube_length, lines_per_block=cube_length, symbols_per_line=cube_length
        )
        mock_read_cube_from_disk.assert_called_once_with(cube_length)
        mock_split.assert_called_once_with(mock_encoded_strengthened_key, expected_number_of_graphemes=44)
        mock_generate_rotors.assert_called_once_with(
            mock_encoded_strengthened_key, mock_cube, num_rotors_to_make=num_rotors_to_make, rotors_to_use=rotors_to_use, orig_key_length=len(key_phrase)
        )
        mock_read_reflector.assert_called_once_with(cube_length)

    @patch("cubigma.cubigma.read_reflector_from_file")
    @patch("cubigma.cubigma.generate_rotors")
    @patch("cubigma.cubigma.split_to_human_readable_symbols")
    @patch("cubigma.cubigma.strengthen_key")
    def test_prepare_machine_valid_inputs(
        self, mock_strengthen_key, mock_split, mock_generate_rotors, mock_read_reflector
    ):
        # Arrange
        (
            cubigma,
            expected_num_unique_quartets,
            key_phrase,
            cube_length,
            num_rotors_to_make,
            rotors_to_use,
            should_use_steganography,
            expected_salt,
            mock_read_characters_file,
            mock_write_cube_file,
            mock_symbols,
            mock_read_cube_from_disk,
            mock_encoded_strengthened_key,
            mock_cube,
        ) = self.configure(mock_strengthen_key, mock_split, mock_generate_rotors)

        # Act
        result_salt = cubigma.prepare_machine(
            key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography
        )

        # Assert
        self.validate(
            cubigma,
            should_use_steganography,
            expected_salt,
            result_salt,
            mock_read_characters_file,
            mock_write_cube_file,
            cube_length,
            mock_symbols,
            mock_read_cube_from_disk,
            mock_split,
            mock_encoded_strengthened_key,
            mock_generate_rotors,
            mock_cube,
            num_rotors_to_make,
            rotors_to_use,
            mock_read_reflector,
            expected_num_unique_quartets,
            key_phrase
        )
        mock_strengthen_key.assert_called_once_with(key_phrase, salt=None)

    @patch("cubigma.cubigma.read_reflector_from_file")
    @patch("cubigma.cubigma.generate_rotors")
    @patch("cubigma.cubigma.split_to_human_readable_symbols")
    @patch("cubigma.cubigma.strengthen_key")
    def test_prepare_machine_valid_inputs_and_salt(
        self, mock_strengthen_key, mock_split, mock_generate_rotors, mock_read_reflector
    ):
        # Arrange
        (
            cubigma,
            expected_num_unique_quartets,
            key_phrase,
            cube_length,
            num_rotors_to_make,
            rotors_to_use,
            should_use_steganography,
            expected_salt,
            mock_read_characters_file,
            mock_write_cube_file,
            mock_symbols,
            mock_read_cube_from_disk,
            mock_encoded_strengthened_key,
            mock_cube,
        ) = self.configure(mock_strengthen_key, mock_split, mock_generate_rotors)

        # Act
        result_salt = cubigma.prepare_machine(
            key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography, salt=expected_salt
        )

        # Assert
        self.validate(
            cubigma,
            should_use_steganography,
            expected_salt,
            result_salt,
            mock_read_characters_file,
            mock_write_cube_file,
            cube_length,
            mock_symbols,
            mock_read_cube_from_disk,
            mock_split,
            mock_encoded_strengthened_key,
            mock_generate_rotors,
            mock_cube,
            num_rotors_to_make,
            rotors_to_use,
            mock_read_reflector,
            expected_num_unique_quartets,
            key_phrase
        )
        mock_strengthen_key.assert_called_once_with(key_phrase, salt=expected_salt.encode("utf-8"))

    @patch("cubigma.cubigma.split_to_human_readable_symbols")
    @patch("cubigma.cubigma.strengthen_key")
    def test_prepare_machine_invalid_key_character(self, mock_strengthen_key, mock_split):
        cubigma = Cubigma()
        mock_read_characters_file = MagicMock()
        mock_symbols = ["a", "b"]
        mock_read_characters_file.return_value = mock_symbols
        cubigma._read_characters_file = mock_read_characters_file  # pylint:disable=W0212
        mock_write_cube_file = MagicMock()
        cubigma._write_cube_file = mock_write_cube_file  # pylint:disable=W0212
        mock_read_cube_from_disk = MagicMock()
        mock_cube = ["A", "C"]
        mock_read_cube_from_disk.return_value = mock_cube
        cubigma._read_cube_from_disk = mock_read_cube_from_disk  # pylint:disable=W0212
        mock_encoded_strengthened_key = "1"
        mock_encoded_strengthened_key_encoded = mock_encoded_strengthened_key.encode("utf-8")
        mock_salt_encoded = "2".encode("utf-8")
        mock_strengthen_key.return_value = mock_encoded_strengthened_key_encoded, mock_salt_encoded
        test_char_not_in_symbols = "7"
        mock_split.return_value = test_char_not_in_symbols

        key_phrase = "invalidKey#@!"
        cube_length = 3
        num_rotors_to_make = 2
        rotors_to_use = [0, 1]
        should_use_steganography = False

        with self.assertRaises(ValueError) as context:
            cubigma.prepare_machine(
                key_phrase, cube_length, num_rotors_to_make, rotors_to_use, should_use_steganography
            )
        self.assertIn("Key was strengthened to include an invalid character", str(context.exception))


class TestMainFunction(unittest.TestCase):
    @patch("cubigma.cubigma.Cubigma")
    @patch("cubigma.cubigma.parse_arguments")
    def test_main_encrypt_mode(self, mock_parse_arguments, mock_cubigma):
        # Arrange
        mock_parse_arguments.return_value = (
            "test_key",  # key_phrase
            "encrypt",  # mode
            "test_message",  # message
            3,  # cube_length
            5,  # num_rotors_to_make
            [1, 2],  # rotors_to_use
            True,  # should_use_steganography
        )
        mock_cubigma_instance = MagicMock()
        mock_cubigma.return_value = mock_cubigma_instance
        mock_cubigma_instance.prepare_machine.return_value = "mock_salt"
        expected_encrypted_message = "encrypted_foo"
        mock_cubigma_instance.encrypt_message.return_value = expected_encrypted_message

        # Act
        with patch("builtins.print") as mock_print:
            main()

        # Assert
        mock_cubigma_instance.prepare_machine.assert_called_once_with("test_key", 3, 5, [1, 2], True, salt=None)
        mock_cubigma_instance.encrypt_message.assert_called_once_with("test_message", "test_key")
        mock_print.assert_any_call("clear_text_message='test_message'")
        mock_print.assert_any_call(f"encrypted_message='mock_salt{expected_encrypted_message}'")
        assert mock_print.call_count == 2

    @patch("cubigma.cubigma.Cubigma")
    @patch("cubigma.cubigma.parse_arguments")
    def test_main_decrypt_mode(self, mock_parse_arguments, mock_cubigma):
        # Arrange
        mock_parse_arguments.return_value = (
            "test_key",  # key_phrase
            "decrypt",  # mode
            "test_encrypted_message",  # message
            3,  # cube_length
            5,  # num_rotors_to_make
            [1, 2],  # rotors_to_use
            True,  # should_use_steganography
        )
        mock_cubigma_instance = MagicMock()
        mock_cubigma.return_value = mock_cubigma_instance
        expected_decrypted_message = "decrypted_foo"
        mock_cubigma_instance.decrypt_message.return_value = expected_decrypted_message

        # Act
        with patch("builtins.print") as mock_print:
            main()

        # Assert
        mock_cubigma_instance.prepare_machine.assert_called_once_with("test_key", 3, 5, [1, 2], True, salt="")
        mock_cubigma_instance.decrypt_message.assert_called_once_with("test_encrypted_message", "test_key")
        mock_print.assert_any_call("encrypted_message='test_encrypted_message'")
        mock_print.assert_any_call(f"decrypted_message='{expected_decrypted_message}'")

    def test_main_unexpected_mode(self):
        with patch("cubigma.cubigma.parse_arguments") as mock_parse_arguments:
            mock_parse_arguments.return_value = (
                "test_key",  # key_phrase
                "invalid_mode",  # mode
                "test_message",  # message
                3,  # cube_length
                5,  # num_rotors_to_make
                [1, 2],  # rotors_to_use
                True,  # should_use_steganography
            )

            with self.assertRaises(ValueError) as context:
                main()

            self.assertEqual(str(context.exception), "Unexpected mode!")


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
