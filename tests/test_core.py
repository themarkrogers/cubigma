# pylint: disable=missing-function-docstring, missing-module-docstring, missing-class-docstring

import base64
import os
import unittest

from cubigma.core import strengthen_key


class TestStrengthenKey(unittest.TestCase):
    # ToDo: These unit tests should have mocks
    def test_key_generation_with_salt(self):
        """Test that strengthen_key generates a key when a salt is provided."""
        key_phrase = "test-key"
        raw_salt = "foo"
        salt = raw_salt.encode("utf-8")
        key, returned_salt = strengthen_key(key_phrase, salt=salt)
        salt_decoded_bytes = base64.b64decode(returned_salt)
        found_plaintext_salt = salt_decoded_bytes.decode("utf-8")

        self.assertIsInstance(key, str)
        self.assertIsInstance(returned_salt, str)
        self.assertEqual("XtH9sWH8YNx+oE4swUlyj5NQiSR/ezjrBa/GGl84HTE=", key)
        self.assertEqual("Zm9v", returned_salt)
        self.assertEqual(len(returned_salt), 4)
        self.assertEqual(raw_salt, found_plaintext_salt)

    def test_key_generation_without_salt(self):
        """Test that strengthen_key generates a key and random salt when no salt is provided."""
        key_phrase = "test-key"
        key, salt = strengthen_key(key_phrase)

        self.assertIsInstance(key, str)
        self.assertIsInstance(salt, str)
        self.assertEqual(len(salt), 24)

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

    def test_key_length_parameter(self):
        """Test that the derived key length matches the specified key_length."""
        key_phrase = "test-key"
        key_length = 64
        returned_key, _ = strengthen_key(key_phrase, key_length=key_length)
        key_decoded_bytes = base64.b64decode(returned_key)

        self.assertEqual(len(key_decoded_bytes), key_length)

    def test_invalid_key_phrase_type(self):
        """Test that passing a non-string key phrase raises a TypeError."""
        with self.assertRaises(AttributeError):
            strengthen_key(12345)  # noqa

    def test_invalid_salt_type(self):
        """Test that passing a non-bytes salt raises a TypeError."""
        with self.assertRaises(TypeError):
            strengthen_key("test-key", salt="invalid-salt")  # noqa

    def test_invalid_iterations_value(self):
        """Test that invalid iteration counts raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", iterations=-1)

    def test_invalid_key_length(self):
        """Test that invalid key lengths raise a ValueError."""
        with self.assertRaises(ValueError):
            strengthen_key("test-key", key_length=0)


# pylint: enable=missing-function-docstring, missing-module-docstring, missing-class-docstring


if __name__ == "__main__":
    unittest.main()
