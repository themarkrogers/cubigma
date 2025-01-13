# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, mock_open, MagicMock
import os
import unittest

from cubigma.cubigma import Cubigma


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
        cubigma._run_quartet_through_rotors = mock_run_quartet_through_rotors
        mock_run_quartet_through_reflector = MagicMock()
        mock_run_quartet_through_reflector.return_value = expected_middle_str
        cubigma._run_quartet_through_reflector = mock_run_quartet_through_reflector
        test_key_phrase = "foo"

        # Act
        result = cubigma._get_encrypted_letter_quartet(test_char_quartet, test_key_phrase)

        # Assert
        self.assertEqual(expected_result, result)
        mock_run_quartet_through_reflector.assert_called_once_with(expected_str_1)


class TestReadCharactersFile(unittest.TestCase):
    def setUp(self):
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
        self.cube_length = 4

    @patch("builtins.open")
    def test_valid_file(self, mock_open_func):
        # Arrange
        num_of_symbols = self.cube_length * self.cube_length * self.cube_length
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

    @patch("builtins.open")
    def test_invalid_file_symbol_length(self, mock_open_func):
        # Arrange
        num_of_symbols = self.cube_length * self.cube_length * self.cube_length
        mock_data = "\n".join(self.symbols[i] for i in range(len(self.symbols)))
        mock_data = mock_data.replace("a", "aA")
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        with self.assertRaises(ValueError) as context:
            cubigma._read_characters_file(self.cube_length)  # pylint:disable=W0212

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


class TestReadCuboidFromDisk(unittest.TestCase):

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
        result = obj._read_cube_from_disk(self.cube_length)

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
            obj._read_cube_from_disk(self.cube_length)

        self.assertIn("unexpected", str(context.exception))

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length", side_effect=mock_user_perceived_length)
    def test_empty_file(self, mock_length, mock_open_file):
        # Mock file content (empty file)
        mock_file_content = ""
        mock_open_file.return_value.readlines.return_value = mock_file_content

        obj = Cubigma(self.cube_file_path)
        result = obj._read_cube_from_disk(self.cube_length)

        self.assertEqual(result, [])

    @patch("builtins.open", new_callable=mock_open)
    @patch("cubigma.cubigma.user_perceived_length", side_effect=mock_user_perceived_length)
    def test_incomplete_frame(self, mock_length, mock_open_file):
        # Mock file content with incomplete frame
        mock_file_content = "abc\ndef\n"  # Only 2 lines, 1 line short of a complete frame
        mock_open_file.return_value.read.return_value = mock_file_content

        obj = Cubigma(self.cube_file_path)
        result = obj._read_cube_from_disk(self.cube_length)

        self.assertEqual(result, [])


class TestRunQuartetThroughReflector(unittest.TestCase):

    @patch("cubigma.cubigma.index_to_quartet")
    @patch("cubigma.cubigma.quartet_to_index")
    def test_run_quartet_through_reflector_valid(self, mock_quartet_to_index, mock_index_to_quartet):
        # Arrange
        cubigma = Cubigma()
        cubigma._is_machine_prepared = True
        expected_symbols = "ABC"
        cubigma._symbols = expected_symbols
        expected_quartet_index = 42
        expected_reflected_index = 9001
        mock_reflector = {expected_quartet_index: expected_reflected_index}
        cubigma.reflector = mock_reflector

        mock_quartet_to_index.return_value = expected_quartet_index
        expected_result = "456"
        mock_index_to_quartet.return_value = expected_result
        test_char_quartet = "123"

        # Act
        result = cubigma._run_quartet_through_reflector(test_char_quartet)

        # Assert
        self.assertEqual(expected_result, result)
        mock_quartet_to_index.assert_called_once_with(test_char_quartet, expected_symbols)
        mock_index_to_quartet.assert_called_once_with(expected_reflected_index, expected_symbols)

    def test_run_quartet_through_reflector_invalid(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma._run_quartet_through_reflector("foo")


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
        cubigma._cube_filepath = self.test_filepath

        cubigma._write_cube_file(
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
        cubigma._cube_filepath = self.test_filepath
        mock_length.return_value = 128

        with self.assertRaises(ValueError):
            cubigma._write_cube_file(
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
        cubigma._is_machine_prepared = True
        mock_encode_string = MagicMock()
        mock_encode_string.return_value = "boop"
        cubigma.encode_string = mock_encode_string

        # Act
        result = cubigma.decode_string("foo", "bar")

        # Assert
        self.assertEqual(expected_return_value, result, "return value is not the expected value")
        mock_encode_string.assert_called_once_with("foo", "bar")


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
        cubigma._is_machine_prepared = True
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


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
