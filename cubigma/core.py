from typing import Any, Sequence, TypeVar
import base64
import hashlib
import os
import random


T = TypeVar("T")  # Generic type variable for elements in the sequence


class DeterministicRandomCore:
    """
    This class allows the randomizer to be seeded once and used many times.
    This class only contains deterministic random functions, and all of its random functions are deterministic
    """

    rng: Any

    def __init__(self, strengthened_key_phrase: str):
        self.rng = None
        self.seed_random(strengthened_key_phrase)

    def seed_random(self, strengthened_key_phrase: str) -> None:
        # Derive a deterministic seed from the sanitized_key_phrase
        seed = int(hashlib.sha256(strengthened_key_phrase.encode()).hexdigest(), 16)

        # Initialize a random generator with the deterministic seed
        rng = random.Random(seed)
        self.rng = rng

    def get_random(self): ...

    def get_random_int(self, min_num: int, max_num: int) -> int:
        result = self.rng.randint(min_num, max_num)
        return result

    def shuffle(self, sequence: Sequence[T]) -> list[T]:
        """
        Shuffle a sequence using secrets for cryptographic security.

        Args:
            sequence (Sequence[T]): The input sequence to shuffle.

        Returns:
            list[T]: A securely shuffled list containing the elements of the input sequence.
        """
        # # Hash the key phrase to create a deterministic seed
        # key_hash = hashlib.sha256(sanitized_key_phrase.encode()).digest()
        #
        # # Create an iterator over the bytes of the hashed key, cycling if necessary
        # hash_iter = iter(key_hash * ((len(sequence) // len(key_hash)) + 1))  # Repeat hash bytes as needed
        #
        # # Shuffle the sequence using deterministic randomness
        # shuffled = list(sequence)
        # for i in range(len(shuffled) - 1, 0, -1):
        #     j = deterministic_randbelow(i + 1, hash_iter)
        #     shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        # return shuffled

        shuffled = list(sequence)
        for i in range(len(shuffled) - 1, 0, -1):
            j = self.get_random_int(0, i)  # Generate a random index deterministically
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        return shuffled


def get_independently_deterministic_random_rotor_info(
    combined_seed: str, axis_choices: list[str], direction_choices: list[int], max_num: int
) -> tuple[str, int, int]:
    random.seed(combined_seed)
    axis = random.choice(axis_choices)
    rotate_dir = random.choice(direction_choices)
    slice_idx_to_rotate = random.randint(0, max_num)
    return axis, rotate_dir, slice_idx_to_rotate


def get_hash_of_string_in_bytes(hash_input: str) -> bytes:
    result = hashlib.sha256(hash_input.encode()).digest()
    return result


def get_non_deterministically_random_int(min_num: int, max_num: int) -> int:
    result = random.randint(min_num, max_num)
    return result


def non_deterministically_random_shuffle_in_place(input_to_shuffle: list) -> None:
    random.shuffle(input_to_shuffle)


def shuffle_for_input(strengthened_key_phrase: str, sequence: Sequence[T]) -> list[T]:
    # Derive a deterministic seed from the sanitized_key_phrase
    seed = int(hashlib.sha256(strengthened_key_phrase.encode()).hexdigest(), 16)

    # Initialize a random generator with the deterministic seed
    rng = random.Random(seed)

    shuffled = list(sequence)
    for i in range(len(shuffled) - 1, 0, -1):
        j = rng.randint(0, i)  # Generate a random index deterministically
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def random_int_for_input(strengthened_key_phrase: str, min_num: int, max_num: int) -> int:
    # Derive a deterministic seed from the sanitized_key_phrase
    seed = int(hashlib.sha256(strengthened_key_phrase.encode()).hexdigest(), 16)

    # Initialize a random generator with the deterministic seed
    rng = random.Random(seed)

    result = rng.randint(min_num, max_num)
    return result


def strengthen_key(
    key_phrase: str, salt: None | bytes = None, iterations: int = 200_000, key_length: int = 32
) -> tuple[str, str]:
    """
    Strengthen a user-provided key using Argon2 key derivation.

    Args:
        key_phrase (str): The weak key phrase provided by the user.
        salt (bytes): Optional salt. If None, generates a random 16-byte salt.
        iterations (int): Number of iterations for PBKDF2 (default is 100,000).
        key_length (int): The desired length of the derived key in bytes (default is 32 bytes for 256-bit key).

    Returns:
        bytes: A securely derived key & the salt used
    """
    if salt is None:
        salt = os.urandom(16)  # Use a secure random salt if not provided
    key_phrase_bytes = key_phrase.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", key_phrase_bytes, salt, iterations, dklen=key_length)  # Derived key length
    b64_key = base64.b64encode(key).decode("utf-8")  # always 44 chars long
    b64_salt = base64.b64encode(salt).decode("utf-8")  # always 24 chars long
    return b64_key, b64_salt
