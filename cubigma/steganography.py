"""
This file is used to embed and read Unicode characters from images.
This is usually done after encrypting a message with Cubigma.
"""

import math
import os

from PIL import Image


def _encode_character(pixel: tuple[int, int, int], char: str) -> tuple[int, int, int]:
    # Helper function to encode a character into the least significant bit of a pixel
    ascii_val = ord(char)  # Ranges from 000006 to 129782
    old_encode_val = (
        (pixel[0] & ~1) | ((ascii_val >> 2) & 1),
        (pixel[1] & ~1) | ((ascii_val >> 1) & 1),
        (pixel[2] & ~1) | (ascii_val & 1),
    )
    ascii_str = str(ascii_val).zfill(6)
    assert len(ascii_str) == 6, f"Unexpected ASCII number found for symbol: {char}"
    r_val = int(ascii_str[0:2])
    g_val = int(ascii_str[2:4])
    b_val = int(ascii_str[4:])
    return r_val, g_val, b_val


def _embed_square(start_x: int, start_y: int, chunk: str, square_size: int, pixels):
    # Helper function to embed a 2D array of characters into a specified region
    idx = 0
    for y in range(start_y, start_y + square_size):
        for x in range(start_x, start_x + square_size):
            if idx < len(chunk):
                new_pixel_value = _encode_character(pixels[x, y], chunk[idx])
                pixels[x, y] = new_pixel_value
                decoded_character = _decode_character(new_pixel_value)
                idx += 1
    return pixels


def get_image_size(filepath: str) -> tuple[int, int]:
    """
    Get the dimensions of a PNG image.

    Args:
        filepath (str): Path to the PNG image.

    Returns:
        tuple[int, int]: A tuple containing the width and height of the image.
    """
    with Image.open(filepath) as img:
        return img.size  # Returns (width, height)


def embed_chunks(encrypted_chunks: list[str], original_image_filepath: str) -> None:
    """
    Given four corners of a rectangular cube, find the other four corners.

    Args:
        encrypted_chunks: List of 5 encrypted text strings to embed into the image
        original_image_filepath: Filepath to the image to use for embedding

    Returns:
        None
    """

    # ToDo: Instead of always embedded at the corners and center, surround each square with a boundary, and stick it
    #   anywhere in the image. This allows us to use more than 5 squares, if the image will fit them.

    # Assert that the original_image_filepath is a PNG file
    if not original_image_filepath.lower().endswith(".png"):
        raise ValueError("The original_image_filepath must point to a PNG file.")

    # Open the original image
    original_image: Image.Image = Image.open(original_image_filepath)
    if original_image.mode != "RGB":
        original_image = original_image.convert("RGB")

    width, height = original_image.size
    pixels = original_image.load()

    # Calculate minimum square dimensions for each chunk
    chunk_sizes = [math.ceil(math.sqrt(len(chunk))) for chunk in encrypted_chunks]

    # Ensure the squares fit in the image and do not overlap
    if chunk_sizes[0] + chunk_sizes[1] > width or chunk_sizes[2] + chunk_sizes[3] > width:
        raise ValueError("The chunks cannot fit into the top/bottom rows without overlap.")
    if chunk_sizes[0] + chunk_sizes[2] > height or chunk_sizes[1] + chunk_sizes[3] > height:
        raise ValueError("The chunks cannot fit into the left/right columns without overlap.")

    # Embed the chunks in the specified regions
    pixels = _embed_square(0, 0, encrypted_chunks[0], chunk_sizes[0], pixels)  # Top-left
    pixels = _embed_square(width - chunk_sizes[1], 0, encrypted_chunks[1], chunk_sizes[1], pixels)  # Top-right
    pixels = _embed_square(0, height - chunk_sizes[2], encrypted_chunks[2], chunk_sizes[2], pixels)  # Bottom-left
    pixels = _embed_square(
        width - chunk_sizes[3], height - chunk_sizes[3], encrypted_chunks[3], chunk_sizes[3], pixels
    )  # Bottom-right

    # Embed the center chunk
    center_start_x = (width - chunk_sizes[4]) // 2
    center_start_y = (height - chunk_sizes[4]) // 2
    pixels = _embed_square(center_start_x, center_start_y, encrypted_chunks[4], chunk_sizes[4], pixels)

    # Save the modified image to disk with "_data" appended to the filename
    new_filepath = f"{os.path.splitext(original_image_filepath)[0]}.data.png"
    original_image.save(new_filepath)

    print(f"Image with embedded data saved as {new_filepath}")


def _decode_character(pixel: tuple[int, int, int]) -> str:
    # Helper function to decode a character from the least significant bit of a pixel

    ascii_val = ((pixel[0] & 1) << 2) | ((pixel[1] & 1) << 1) | (pixel[2] & 1)
    old_decode_val = chr(ascii_val)

    r_val = str(pixel[0]).zfill(2)
    g_val = str(pixel[1]).zfill(2)
    b_val = str(pixel[2]).zfill(2)
    ascii_code = int(r_val + g_val + b_val)
    char = chr(ascii_code)
    return char


def _extract_square(start_x: int, start_y: int, square_size: int, pixels) -> str:
    # Helper function to extract a 2D square of characters from a specified region
    chunk = []
    for y in range(start_y, start_y + square_size):
        for x in range(start_x, start_x + square_size):
            chunk.append(_decode_character(pixels[x, y]))
    return "".join(chunk)


def _discover_square_size(start_x: int, start_y: int, width: int, height: int, pixels):
    # Discover the square sizes by searching for atypical data in corners and center
    size = 1
    while (
        start_x + size < width
        and start_y + size < height
        and _decode_character(pixels[start_x + size, start_y + size]) != "\x00"
    ):
        size += 1
    return size


def get_chunks_from_image(stego_image_filepath: str) -> list[str]:
    """
    Get the 5 embedded message chunks from the image provided.

    Args:
        stego_image_filepath: Filepath to the image with an embedded message

    Returns:
        5 encrypted message chunks
    """
    if not stego_image_filepath.lower().endswith(".png"):
        raise ValueError("The stego_image_filepath must point to a PNG file.")

    stego_image: Image.Image = Image.open(stego_image_filepath)
    if stego_image.mode != "RGB":
        stego_image = stego_image.convert("RGB")

    width, height = stego_image.size
    pixels = stego_image.load()

    # Top-left corner (chunk_1)
    size_top_left = _discover_square_size(0, 0, width, height, pixels)
    chunk_1 = _extract_square(0, 0, size_top_left, pixels)

    # Top-right corner (chunk_2)
    size_top_right = _discover_square_size(width - 1, 0, width, height, pixels)
    chunk_2 = _extract_square(width - size_top_right, 0, size_top_right, pixels)

    # Bottom-left corner (chunk_3)
    size_bottom_left = _discover_square_size(0, height - 1, width, height, pixels)
    chunk_3 = _extract_square(0, height - size_bottom_left, size_bottom_left, pixels)

    # Bottom-right corner (chunk_4)
    size_bottom_right = _discover_square_size(width - 1, height - 1, width, height, pixels)
    chunk_4 = _extract_square(width - size_bottom_right, height - size_bottom_right, size_bottom_right, pixels)

    # Center (chunk_5)
    center_start_x = (width - size_top_left) // 2
    center_start_y = (height - size_top_left) // 2
    size_center = _discover_square_size(center_start_x, center_start_y, width, height, pixels)
    chunk_5 = _extract_square(center_start_x, center_start_y, size_center, pixels)

    return [chunk_1, chunk_2, chunk_3, chunk_4, chunk_5]


def encode_image(image_path: str, output_path: str, message: str) -> None:
    """
    Encodes a message into an image using the least significant bit (LSB) method.
    """
    image = Image.open(image_path)
    if image.mode != "RGB":
        raise ValueError("Image mode must be RGB")

    pixels = image.load()
    binary_message = "".join(f"{ord(c):08b}" for c in message) + "00000000"
    binary_index = 0

    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]

            if binary_index < len(binary_message):
                r = (r & ~1) | int(binary_message[binary_index])
                binary_index += 1
            if binary_index < len(binary_message):
                g = (g & ~1) | int(binary_message[binary_index])
                binary_index += 1
            if binary_index < len(binary_message):
                b = (b & ~1) | int(binary_message[binary_index])
                binary_index += 1

            pixels[x, y] = (r, g, b)
            if binary_index >= len(binary_message):
                break
        if binary_index >= len(binary_message):
            break

    image.save(output_path)
    print(f"Message encoded and saved to {output_path}")


def decode_image(image_path: str) -> str:
    """
    Decodes a hidden message from an image using the least significant bit (LSB) method.
    """
    image = Image.open(image_path)
    if image.mode != "RGB":
        raise ValueError("Image mode must be RGB")

    pixels = image.load()
    binary_message = ""

    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            binary_message += str(r & 1)
            binary_message += str(g & 1)
            binary_message += str(b & 1)

    message = ""
    for i in range(0, len(binary_message), 8):
        end_idx = i + 8
        byte = binary_message[i:end_idx]
        if byte == "00000000":
            break
        message += chr(int(byte, 2))

    return message


if __name__ == "__main__":
    encode_image("kitten.jpg", "kitten.data.jpg", "Andy is married to Liz. Hoo-ah")
    decoded_message = decode_image("kitten.data.jpg")
    print(f"Decoded message: {decoded_message}")
