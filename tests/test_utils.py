from unittest.mock import patch
import json
import unittest

from cubigma.utils import read_config, user_perceived_length


class TestUserPerceivedLength(unittest.TestCase):
    def test_basic_text(self):
        self.assertEqual(user_perceived_length("hello"), 5)
        self.assertEqual(user_perceived_length(""), 0)
        self.assertEqual(user_perceived_length("a"), 1)

    def test_emojis(self):
        self.assertEqual(user_perceived_length("🙂"), 1)
        self.assertEqual(user_perceived_length("🙂🙂"), 2)

    def test_surrogate_pairs(self):
        self.assertEqual(user_perceived_length("👨‍👩‍👧‍👦"), 1)  # Family emoji
        self.assertEqual(user_perceived_length("👩‍❤️‍💋‍👨"), 1)  # Couple kissing emoji

    def test_combining_characters(self):
        self.assertEqual(user_perceived_length("á"), 1)  # "á" as 'a' + combining acute accent
        self.assertEqual(user_perceived_length("éé"), 2)  # Two "é"
        self.assertEqual(user_perceived_length("é́"), 1)  # One "e" with two combining marks

    def test_mixed_content(self):
        self.assertEqual(user_perceived_length("hello🙂"), 6)
        self.assertEqual(user_perceived_length("🙂á"), 2)
        self.assertEqual(user_perceived_length("🙂👩‍❤️‍💋‍👨"), 2)


class TestReadConfig(unittest.TestCase):
    def setUp(self):
        # Sample valid configuration data
        self.valid_config = {
            "key1": "value1",
            "key2": 42,
            "key3": [1, 2, 3]
        }

    @patch("cubigma.utils.Path")
    @patch("cubigma.utils.json.load")
    def test_read_valid_config(self, mock_load, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = True
        mock_load.return_value = {'key1': 'value1', 'key2': 42, 'key3': [1, 2, 3]}

        # Act
        config = read_config("mock_config.json")

        # Assert
        self.assertEqual(config, self.valid_config)
        mock_path.return_value.open.assert_called_once_with("r", encoding="utf-8")
        mock_load.assert_called_once()

    @patch("cubigma.utils.Path")
    def test_missing_config_file(self, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = False

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            read_config("missing_config.json")

    @patch("cubigma.utils.Path")
    def test_invalid_json_format(self, mock_path):
        # Arrange
        mock_path.return_value.is_file.return_value = True
        mock_path.return_value.open.return_value.__enter__.return_value.read.return_value = "{'Not valid json'"

        # Act & Assert
        with self.assertRaises(json.JSONDecodeError):
            read_config("invalid_config.json")
        mock_path.return_value.open.assert_called_once_with("r", encoding="utf-8")
        mock_path.return_value.open.return_value.__enter__.return_value.read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
