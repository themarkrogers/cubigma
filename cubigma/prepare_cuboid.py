"""
This file is used to convert characters.txt into cuboid.txt based on the three constants in config.json.
This is Step 1 in The Cubigma encryption algorithm.
"""

from utils import read_config, user_perceived_length

config = read_config()
SYMBOLS_PER_LINE = config["SYMBOLS_PER_LINE"]
LINES_PER_BLOCK = config["LINES_PER_BLOCK"]
NUM_BLOCKS = config["NUM_BLOCKS"]


def _sanitize(raw_input: str) -> str:
    if raw_input.startswith("\\"):
        return raw_input.strip().replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return raw_input.replace("\n", "")


def _read_characters_file(characters_file_name: str = "characters.txt") -> list[str]:
    with open(characters_file_name, "r", encoding="utf-8") as line_count_file:
        num_symbols_prepared = sum(1 for _ in line_count_file)

    symbols_to_load = SYMBOLS_PER_LINE * LINES_PER_BLOCK * NUM_BLOCKS
    symbols_loaded = 0
    if symbols_to_load > num_symbols_prepared:
        raise ValueError(
            f"Not enough symbols are prepared. {num_symbols_prepared} symbols prepared. "
            + f"Requested a cuboid with {symbols_to_load} symbols. "
        )
    symbols = []
    with open(characters_file_name, "r", encoding="utf-8") as file:
        for line in file.readlines():
            len_before = len(symbols)
            found_symbol = _sanitize(line)
            symbols.append(found_symbol)
            len_after = len(symbols)
            if len_before == len_after:
                print(f"Duplicate symbol found: {found_symbol}")
            symbols_loaded += 1
            if symbols_loaded >= symbols_to_load:
                break
    symbols_per_block = SYMBOLS_PER_LINE * LINES_PER_BLOCK
    total_num_of_symbols = symbols_per_block * NUM_BLOCKS

    if len(symbols) != total_num_of_symbols:
        raise ValueError(
            f"The file must contain exactly {total_num_of_symbols} symbols, one per line. Found {len(symbols)}"
        )

    # Reverse, so the least common symbols are first; this helps entropy when loading the key phrase
    symbols = list(reversed(symbols))
    return symbols


def _write_cuboid_file(symbols: list[str], output_file_name: str = "cube.txt") -> None:
    symbols_per_block = SYMBOLS_PER_LINE * LINES_PER_BLOCK
    output_lines = []
    for block in range(NUM_BLOCKS):
        for row in range(LINES_PER_BLOCK):
            start_idx = block * symbols_per_block + row * SYMBOLS_PER_LINE
            end_idx = block * symbols_per_block + (row + 1) * SYMBOLS_PER_LINE
            line = "".join(symbols[start_idx:end_idx])
            if user_perceived_length(line) != SYMBOLS_PER_LINE:
                raise ValueError("Something has failed")
            sanitized_line = line.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
            output_lines.append(sanitized_line)
        output_lines.append("")  # Add an empty line between blocks
    with open(output_file_name, "w", encoding="utf-8") as file:
        file.write("\n".join(output_lines))


def reformat_characters(input_characters_file: str = "characters.txt", output_cuboid_file: str = "cuboid.txt") -> None:
    """
    Convert characters.txt into cuboid.txt based on the three constants defined in config.json.
    This is Step 1 in The Cubigma encryption algorithm.

    Args:
        input_characters_file (str): Path to the input characters.txt file.
        output_cuboid_file (str): Path to the output cuboid.txt file.

    Returns:
        None
    """
    symbols = _read_characters_file(characters_file_name=input_characters_file)
    _write_cuboid_file(symbols, output_file_name=output_cuboid_file)
    print(f"File successfully shuffled and written to: {output_cuboid_file}")


if __name__ == "__main__":
    reformat_characters()
