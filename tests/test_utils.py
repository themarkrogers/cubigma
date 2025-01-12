import unittest

from cubigma.utils import user_perceived_length


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


if __name__ == "__main__":
    unittest.main()
