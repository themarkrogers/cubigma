from unittest.mock import patch
import unittest

from cubigma.cubigma import Cubigma
from cubigma.cubigma import _sanitize  # pylint: disable=W0212


class TestSanitizeFunction(unittest.TestCase):
    def test_escape_sequences(self):
        """Test if escape sequences are properly converted."""
        # Act & Assert
        self.assertEqual(_sanitize("\\n"), "\n", "Failed to convert newline escape sequence.")
        self.assertEqual(_sanitize("\\t"), "\t", "Failed to convert tab escape sequence.")
        self.assertEqual(_sanitize("\\\\"), "\\", "Failed to convert backslash escape sequence.")

    def test_mixed_escape_sequences(self):
        """Test if mixed escape sequences are handled correctly."""
        input_str = "\\nSome\\tText\\\\Here"
        expected_output = "\nSome\tText\\Here"

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle mixed escape sequences.")

    def test_plain_string(self):
        """Test if a plain string without leading backslash is returned unchanged except for newline removal."""
        input_str = "This is a test string.\nWith newline."
        expected_output = "This is a test string.With newline."

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle plain string correctly.")

    def test_string_with_no_modifications(self):
        """Test if a string without newlines or leading backslash is returned unchanged."""
        input_str = "This is a test string."
        expected_output = "This is a test string."

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle string with no modifications.")

    def test_empty_string(self):
        """Test if an empty string is handled correctly."""
        input_str = ""
        expected_output = ""

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle empty string.")

    def test_leading_backslash_with_plain_text(self):
        """Test if leading backslash with plain text is handled correctly."""
        input_str = "\\Hello"
        expected_output = "\\Hello"

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle leading backslash with plain text.")

    def test_only_backslashes(self):
        """Test if a string with only backslashes is handled correctly."""
        input_str = "\\\\\\"
        expected_output = "\\\\"

        # Act & Assert
        self.assertEqual(_sanitize(input_str), expected_output, "Failed to handle string with only backslashes.")


class TestReadCharactersFile(unittest.TestCase):
    @patch("builtins.open")
    def test_valid_file(self, mock_open):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols))
        mock_open.return_value = mock_open(mock=mock_open, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file()

        # Assert
        expected_symbols = list(reversed([f"symbol{i}" for i in range(num_of_symbols)]))
        self.assertEqual(result, expected_symbols)

    @patch("builtins.open")
    def test_missing_file(self, mock_open):
        # Arrange
        mock_open.side_effect = FileNotFoundError

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            cubigma = Cubigma("missing.txt", "")
            cubigma._read_characters_file()


    @patch("builtins.open")
    def test_insufficient_symbols(self, mock_open):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        mock_data = "\n".join(f"symbol{i}" for i in range(num_of_symbols - 1))
        mock_open.return_value = mock_open(mock=mock_open, read_data=mock_data).return_value

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            cubigma = Cubigma("characters.txt", "")
            cubigma._read_characters_file()
        self.assertIn("Not enough symbols are prepared", str(context.exception))

    @patch("builtins.open")
    def test_duplicate_symbols(self, mock_open):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        mock_data = "\n".join(f"symbol{i // 2}" for i in range(num_of_symbols))
        mock_open.return_value = mock_open(mock=mock_open, read_data=mock_data).return_value

        # Act & Assert
        with patch("builtins.print") as mock_print:
            cubigma = Cubigma("characters.txt", "")
            result = cubigma._read_characters_file()
            mock_print.assert_called()  # Check if duplicate symbols were reported

    @patch("builtins.open")
    def test_exact_symbols_with_empty_lines(self, mock_open):
        # Arrange
        num_of_symbols = 3 * 4 * 5
        symbols = [f"symbol{i}" for i in range(num_of_symbols)]
        mock_data = "\n".join(symbols + ["" for _ in range(5)])
        mock_open.return_value = mock_open(mock=mock_open, read_data=mock_data).return_value

        # Act
        cubigma = Cubigma("characters.txt", "")
        result = cubigma._read_characters_file()

        # Assert
        expected_symbols = list(reversed(symbols))
        self.assertEqual(result, expected_symbols)


if __name__ == "__main__":
    unittest.main()
