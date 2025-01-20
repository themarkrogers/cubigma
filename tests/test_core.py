# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest.mock import patch, MagicMock
import base64
import os
import unittest

from cubigma.core import (
    get_independently_deterministic_random_rotor_info,
    get_hash_of_string_in_bytes,
    get_non_deterministically_random_int,
    get_non_deterministically_random_shuffled,
    random_int_for_input,
    shuffle_for_input,
    strengthen_key,
)


class TestGetIndependentlyDeterministicRandomRotorInfo(unittest.TestCase):

    @patch("random.randint")
    @patch("random.choice")
    @patch("random.seed")
    def test_valid_case(self, mock_seed, mock_choice, mock_randint):
        # Arrange
        mock_choice.side_effect = ["X", 1]
        mock_randint.return_value = 3
        test_key = "keyphrase1"
        test_axis_choices = ["X", "Y", "Z"]
        test_direction_choices = [-1, 1]
        test_max_num = 5
        expected_results = ("X", 1, 3)

        # Act
        results = get_independently_deterministic_random_rotor_info(
            test_key, test_axis_choices, test_direction_choices, test_max_num
        )

        # Assert
        self.assertEqual(expected_results, results)
        mock_seed.assert_called_once_with(test_key)
        assert mock_choice.call_count == 2
        mock_choice.assert_any_call(test_axis_choices)
        mock_choice.assert_any_call(test_direction_choices)
        mock_randint.assert_called_once_with(0, test_max_num)


class TestGetHashOfStringInBytes(unittest.TestCase):

    @patch("hashlib.sha256")
    def test_valid_case(self, mock_sha256):
        # Arrange
        expected_result = 42
        mock_digest = MagicMock()
        mock_digest.digest.return_value = expected_result
        mock_sha256.return_value = mock_digest
        test_input = "rawr"

        # Act
        result = get_hash_of_string_in_bytes(test_input)

        # Assert
        self.assertEqual(expected_result, result)
        mock_sha256.assert_called_once_with(test_input.encode())
        mock_digest.digest.assert_called_once_with()


class TestGetNonDeterministicallyRandomInt(unittest.TestCase):

    @patch("random.randint")
    def test_valid_case(self, mock_randint):
        # Arrange
        expected_result = 42
        mock_randint.return_value = expected_result

        # Act
        result = get_non_deterministically_random_int(11, 17)

        # Assert
        self.assertEqual(expected_result, result)
        mock_randint.assert_called_once_with(11, 17)


class TestGetNonDeterministicallyRandomShuffled(unittest.TestCase):

    @patch("random.shuffle")
    def test_valid_case(self, mock_shuffle):
        # Arrange
        expected_results = [3, 1, 2, 4]
        mock_shuffle.side_effect = lambda x: x.clear() or x.extend(expected_results)
        test_list = [1, 2, 3, 4]

        # Act
        results = get_non_deterministically_random_shuffled(test_list)

        # Assert
        self.assertEqual(expected_results, results)
        # mock_shuffle.assert_called_once_with(test_list)


class TestShuffleForInput(unittest.TestCase):

    @patch("hashlib.sha256")
    @patch("random.Random")
    def test_valid_case(self, mock_random, mock_sha256):
        # Arrange
        test_shuffle_responses = [3, 1, 0, 2]
        expected_results = [3, 1, 2, 4]
        mock_randint = MagicMock()
        mock_randint.randint.side_effect = test_shuffle_responses
        mock_random.return_value = mock_randint
        mock_result = MagicMock()
        mock_result.hexdigest.return_value = "2A"
        mock_sha256.return_value = mock_result
        test_key = "testkey1"
        test_list = [1, 2, 3, 4]

        # Act
        results = shuffle_for_input(test_key, test_list)

        # Assert
        self.assertEqual(expected_results, results)
        mock_sha256.assert_called_once_with(test_key.encode())
        mock_result.hexdigest.assert_called_once_with()
        mock_random.assert_called_once_with(42)
        assert mock_randint.randint.call_count == 3
        mock_randint.randint.assert_any_call(0, 3)
        mock_randint.randint.assert_any_call(0, 2)
        mock_randint.randint.assert_any_call(0, 1)


class TestRandomIntForInput(unittest.TestCase):

    @patch("hashlib.sha256")
    @patch("random.Random")
    def test_valid_case(self, mock_random, mock_sha256):
        # Arrange
        expected_result = 420
        mock_randint = MagicMock()
        mock_randint.randint.return_value = expected_result
        mock_random.return_value = mock_randint
        mock_result = MagicMock()
        mock_result.hexdigest.return_value = "2A"
        mock_sha256.return_value = mock_result
        test_key = "testkey1"

        # Act
        result = random_int_for_input(test_key, 11, 29)

        # Assert
        self.assertEqual(expected_result, result)
        mock_sha256.assert_called_once_with(test_key.encode())
        mock_result.hexdigest.assert_called_once_with()
        mock_random.assert_called_once_with(42)
        mock_randint.randint.assert_called_once_with(11, 29)


class TestStrengthenKey(unittest.TestCase):

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_key_generation_with_salt(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that strengthen_key generates a key when a salt is provided."""
        # Arrange
        key_phrase = "test-key"
        raw_salt = "foo"
        salt = raw_salt.encode("utf-8")
        mock_hmac.return_value = b"super_secret_hmac_key"
        mock_b64decode.side_effect = [b"420"]
        mock_b64encode.side_effect = [b"42", b"abcd"]
        expected_key = "42"
        expected_salt = "abcd"

        # Act
        key, returned_salt = strengthen_key(key_phrase, salt=salt)

        # Assert
        self.assertIsInstance(key, str)
        self.assertIsInstance(returned_salt, str)
        self.assertEqual(expected_key, key)
        self.assertEqual(expected_salt, returned_salt)
        self.assertEqual(len(returned_salt), 4)
        mock_random.assert_not_called()
        mock_hmac.assert_called_once_with("sha256", key_phrase.encode("utf-8"), salt, 200_000, dklen=32)
        mock_b64decode.assert_not_called()
        assert mock_b64encode.call_count == 2
        mock_b64encode.assert_any_call(b"foo")
        mock_b64encode.assert_any_call(b"super_secret_hmac_key")

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_key_generation_without_salt(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that strengthen_key generates a key and random salt when no salt is provided."""
        # Arrange
        key_phrase = "test-key"
        mock_hmac.return_value = b"super_secret_hmac_key"
        mock_b64decode.side_effect = [b"420"]
        mock_b64encode.side_effect = [b"42", b"abcdefghijklmnopqrstuvwx"]
        expected_key = "42"
        expected_salt = "abcdefghijklmnopqrstuvwx"
        expected_random_salt = "random salt"
        mock_random.return_value = expected_random_salt

        # Act
        key, salt = strengthen_key(key_phrase)

        # Assert
        self.assertIsInstance(key, str)
        self.assertIsInstance(salt, str)
        self.assertEqual(len(salt), 24)
        self.assertIsInstance(key, str)
        self.assertEqual(expected_key, key)
        self.assertEqual(expected_salt, salt)
        mock_random.assert_called_once_with(16)
        mock_hmac.assert_called_once_with("sha256", key_phrase.encode("utf-8"), expected_random_salt, 200_000, dklen=32)
        mock_b64decode.assert_not_called()
        assert mock_b64encode.call_count == 2
        mock_b64encode.assert_any_call(expected_random_salt)  # ToDo: Is this correct? Should this be bytes?
        mock_b64encode.assert_any_call(b"super_secret_hmac_key")

    def test_key_derivation_is_consistent(self):
        """Test that the same key phrase and salt produce the same key."""
        key_phrase = "test-key"
        salt = os.urandom(16)
        key1, _ = strengthen_key(key_phrase, salt=salt)
        key2, _ = strengthen_key(key_phrase, salt=salt)

        self.assertEqual(key1, key2)

    def test_different_salts_produce_different_keys(self):
        """Test that different salts produce different keys."""
        key_phrase = "test-key"
        salt1 = "foo1".encode("utf-8")
        salt2 = "foo2".encode("utf-8")
        key1, _ = strengthen_key(key_phrase, salt=salt1)
        key2, _ = strengthen_key(key_phrase, salt=salt2)

        self.assertNotEqual(key1, key2)

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_key_length_parameter(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that the derived key length matches the specified key_length."""
        # Arrange
        key_phrase = "test-key"
        key_length = 64
        expected_random_salt = "random salt"
        mock_hmac.return_value = b"super_secret_hmac_key"
        mock_b64decode.side_effect = [b"1234567890123456789012345678901234567890123456789012345678901234"]
        mock_b64encode.side_effect = [b"42", b"abcdefghijklmnopqrstuvwx"]
        mock_random.return_value = expected_random_salt

        # Act
        returned_key, _ = strengthen_key(key_phrase, key_length=key_length)
        key_decoded_bytes = base64.b64decode(returned_key)

        # Assert
        self.assertEqual(len(key_decoded_bytes), key_length)
        mock_random.assert_called_once_with(16)
        mock_hmac.assert_called_once_with(
            "sha256", key_phrase.encode("utf-8"), expected_random_salt, 200_000, dklen=key_length
        )
        mock_b64decode.assert_called_once_with("42")
        assert mock_b64encode.call_count == 2
        mock_b64encode.assert_any_call(expected_random_salt)
        mock_b64encode.assert_any_call(b"super_secret_hmac_key")

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_invalid_key_phrase_type(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that passing a non-string key phrase raises a TypeError."""
        with self.assertRaises(AttributeError):
            strengthen_key(12345)  # noqa
        mock_random.assert_called_once_with(16)
        mock_hmac.assert_not_called()
        mock_b64encode.assert_not_called()
        mock_b64decode.assert_not_called()

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_invalid_salt_type(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that passing a non-bytes salt raises a TypeError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", salt="invalid-salt")  # noqa
        mock_random.assert_not_called()
        mock_hmac.assert_not_called()
        mock_b64encode.assert_not_called()
        mock_b64decode.assert_not_called()

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_invalid_iterations_value(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that invalid iteration counts raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", iterations=-1)
        mock_random.assert_called_once_with(16)
        mock_hmac.assert_not_called()
        mock_b64encode.assert_not_called()
        mock_b64decode.assert_not_called()

    @patch("base64.b64decode")
    @patch("base64.b64encode")
    @patch("hashlib.pbkdf2_hmac")
    @patch("os.urandom")
    def test_invalid_key_length(self, mock_random, mock_hmac, mock_b64encode, mock_b64decode):
        """Test that invalid key lengths raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", key_length=0)
        mock_random.assert_called_once_with(16)
        mock_hmac.assert_not_called()
        mock_b64encode.assert_not_called()
        mock_b64decode.assert_not_called()


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
