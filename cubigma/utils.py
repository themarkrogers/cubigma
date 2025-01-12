""" Useful shared utilities for the cubigma project. """

from pathlib import Path
from typing import Any
import json

import regex

LENGTH_OF_QUARTET = 4
NOISE_SYMBOL = ""


def user_perceived_length(s: str) -> int:
    """
    Used to count the length of strings with surrogate pair emojis

    Args:
        s (str): the string (containing emojis) that needs to be counted

    Returns:
        int: the number of symbols as they would be counted by a human
    """
    # Match grapheme clusters
    graphemes = regex.findall(r"\X", s)
    return len(graphemes)


def read_config(config_file: str = "config.json") -> dict[str, Any]:
    """
    Reads and parses the configuration from the specified JSON file.

    Args:
        config_file (str): The path to the configuration file. Defaults to "config.json".

    Returns:
        dict[str, Any]: The configuration data as a dictionary.
    """
    config_path = Path(config_file)
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)
