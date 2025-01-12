from unittest.mock import patch, mock_open
import unittest

from cubigma.cubigma import Cubigma


class TestReadCharactersFile(unittest.TestCase):
    @patch("builtins.open")
    def test_valid_file(self, mock_open_func):
        # Arrange
        num_of_symbols = 7 * 7 * 7  # ToDo: How do we keep the test passing and change this value?
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file()

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
            cubigma._read_characters_file()

    @patch("builtins.open")
    def test_insufficient_symbols(self, mock_open_func):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols - 1))
        mock_open_func.return_value = mock_open(mock=mock_open_func, read_data=mock_data).return_value

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            cubigma = Cubigma("characters.txt", "")
            cubigma._read_characters_file()
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
            result = cubigma._read_characters_file()
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
        result = cubigma._read_characters_file()

        # Assert
        expected_symbols = list(reversed(symbols))
        self.assertEqual(result, expected_symbols)


if __name__ == "__main__":
    unittest.main()
