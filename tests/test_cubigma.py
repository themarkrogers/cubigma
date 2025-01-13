# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, mock_open, MagicMock
import unittest

from cubigma.cubigma import Cubigma


# Testing Private Cubigma Functions


class TestGetCharsForCoordinates(unittest.TestCase):

    def test_get_chars_for_valid_coordinates(self):
        # Arrange
        cubigma = Cubigma()
        test_rotor = [
            [["1","2",'3'], ["4","5","6"], ["7", "8", "9"]]
        ]
        coordinate = (0, 2, 1)
        expected_result = '8'

        # Act
        result = cubigma._get_chars_for_coordinates(coordinate, test_rotor)

        # Assert
        self.assertEqual(expected_result, result)

    def test_get_chars_for_invalid_coordinates(self):
        # Arrange
        cubigma = Cubigma()
        test_rotor = [
            [["1","2",'3'], ["4","5","6"], ["7", "8", "9"]]
        ]
        coordinate = (1, 0, 2)

        # Act & Assert
        with self.assertRaises(IndexError):
            cubigma._get_chars_for_coordinates(coordinate, test_rotor)


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

        # Act
        result = cubigma._get_encrypted_letter_quartet(test_char_quartet)

        # Assert
        self.assertEqual(expected_result, result)
        mock_run_quartet_through_reflector.assert_called_once_with(expected_str_1)


class TestReadCharactersFile(unittest.TestCase):
    @patch("builtins.open")
    def test_valid_file(self, mock_open_func):
        # Arrange
        num_of_symbols = 7 * 7 * 7  # ToDo: How do we keep the test passing and changes to this value?
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file()  # pylint:disable=W0212

        # Assert
        expected_symbols = list(reversed([f"symbol{i}" for i in range(num_of_symbols)]))
        self.assertEqual(result, expected_symbols)

    @patch("builtins.open")
    def test_missing_file(self, mock_open_func):
        # Arrange
        mock_open_func.side_effect = FileNotFoundError

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            cubigma = Cubigma("missing.txt", "")
            cubigma._read_characters_file()  # pylint:disable=W0212

    @patch("builtins.open")
    def test_insufficient_symbols(self, mock_open_func):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols - 1))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            cubigma = Cubigma("characters.txt", "")
            cubigma._read_characters_file()  # pylint:disable=W0212
        self.assertIn("Not enough symbols are prepared", str(context.exception))

    @patch("builtins.open")
    def test_duplicate_symbols(self, mock_open_func):
        # Arrange
        num_of_symbols = 7 * 7 * 7  # ToDo: How do we keep the test passing and change this value?
        mock_data = "\n".join(f"symbol{i // 2}" for i in range(num_of_symbols))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act & Assert
        with patch("builtins.print") as mock_print:
            cubigma = Cubigma("characters.txt", "")
            result = cubigma._read_characters_file()  # pylint:disable=W0212
            assert mock_print.call_count == 0  # Check if duplicate symbols were reported
            assert len(result) == num_of_symbols

    @patch("builtins.open")
    def test_exact_symbols_with_empty_lines(self, mock_open_func):
        # Arrange
        num_of_symbols = 7 * 7 * 7  # ToDo: How do we keep the test passing and change this value?
        symbols = [f"symbol{i}" for i in range(num_of_symbols)]
        mock_data = "\n".join(symbols + ["" for _ in range(5)])
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file()  # pylint:disable=W0212

        # Assert
        expected_symbols = list(reversed(symbols))
        self.assertEqual(result, expected_symbols)


class TestRunQuartetThroughReflector(unittest.TestCase):

    @patch("cubigma.cubigma.index_to_quartet")
    @patch("cubigma.cubigma.quartet_to_index")
    def test_run_quartet_through_reflector_valid(self, mock_quartet_to_index, mock_index_to_quartet):
        # Arrange
        cubigma = Cubigma()
        cubigma.is_machine_prepared = True
        expected_symbols = "ABC"
        cubigma.symbols = expected_symbols
        expected_quartet_index = 42
        expected_reflected_index = 9001
        mock_reflector = { expected_quartet_index: expected_reflected_index }
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


# Testing Public Cubigma Functions


class TestDecodeString(unittest.TestCase):

    def test_decode_string_before_machine_prepared(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma.decode_string("foo")

    def test_decode_string_valid(self):
        # Arrange
        expected_return_value = "boop"
        cubigma = Cubigma()
        cubigma.is_machine_prepared = True
        mock_encode_string = MagicMock()
        mock_encode_string.return_value = "boop"
        cubigma.encode_string = mock_encode_string

        # Act
        result = cubigma.decode_string("foo")

        # Assert
        self.assertEqual(expected_return_value, result, "return value is not the expected value")
        mock_encode_string.assert_called_once_with("foo")


class TestEncryptMessage(unittest.TestCase):

    def test_encrypt_message_before_machine_prepared(self):
        # Arrange
        cubigma = Cubigma()

        # Act & Assert
        with self.assertRaises(ValueError):
            cubigma.encrypt_message("foo")

    @patch("cubigma.cubigma.prep_string_for_encrypting")
    def test_encrypt_message_valid(self, mock_prep_string_for_encrypting):
        # Arrange
        expected_return_value = "boop"
        cubigma = Cubigma()
        cubigma.is_machine_prepared = True
        expected_string = "bar"
        mock_prep_string_for_encrypting.return_value = expected_string
        mock_encode_string = MagicMock()
        mock_encode_string.return_value = expected_return_value
        cubigma.encode_string = mock_encode_string

        # Act
        result = cubigma.encrypt_message("foo")

        # Assert
        self.assertEqual(expected_return_value, result, "return value is not the expected value")
        mock_encode_string.assert_called_once_with(expected_string)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
