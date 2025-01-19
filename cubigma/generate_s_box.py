import json
import random


def read_characters(file_path="characters.txt"):
    """
    Read 125 symbols (one per line) from `characters.txt`.
    Returns a list of symbols. Index in the list is that symbol's 'ID'.
    """
    chars = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            symbol = line.rstrip("\n")
            if symbol:  # ignore blank lines
                chars.append(symbol)
    # Safety check - expecting exactly 125 symbols
    if len(chars) < 125:
        raise ValueError(f"Expected 125 symbols, found {len(chars)}!")
    return chars[0:125]


def triple_to_index(t0, t1, t2, size=125):
    """
    Given three indices (each in [0..size-1]),
    return the integer in [0..size^3 - 1].
    """
    return t0 * (size**2) + t1 * size + t2


def index_to_triple(idx, size=125):
    """
    Inverse of triple_to_index:
    Given idx in [0..size^3 - 1],
    return (t0, t1, t2) each in [0..size-1].
    """
    t0 = idx // (size**2)
    remainder = idx % (size**2)
    t1 = remainder // size
    t2 = remainder % size
    return (t0, t1, t2)


def build_random_sbox(chars):
    """
    Builds a random S-Box (permutation) over the 125^3 possible 3-symbol blocks.
    Returns:
        sbox: a list of length 125^3 where sbox[x] = y
              and both x, y are integers in [0..125^3 - 1].
    """
    size = len(chars)  # should be 125
    domain_size = size**3

    # Generate a random permutation of the full domain
    permutation = list(range(domain_size))
    random.shuffle(permutation)

    # sbox[x] = permutation[x]
    sbox = permutation  # rename for clarity
    return sbox


def write_sbox_to_file(sbox, file_path="sbox.json"):
    """
    Write the S-Box (list of integers) to a JSON file.
    WARNING: For 125^3 elements, this file will be huge (~ tens of MB).
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sbox, f)


def read_sbox_from_file(file_path="sbox.json"):
    """
    Read the S-Box (list of integers) from a JSON file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        sbox = json.load(f)
    return sbox


def compute_ddt(sbox):
    """
    Naive method to compute the Difference Distribution Table (DDT).

    WARNING: For 125^3 domain, this is huge (on the order of 1e12 ops).
    This function is only feasible for a small domain or for demonstration.

    Returns:
        ddt: a 2D list (or dict) of size N x N, where N = len(sbox).
    """
    N = len(sbox)
    # Initialize DDT with zeros
    ddt = [[0] * N for _ in range(N)]

    for x in range(N):
        sx = sbox[x]
        for delta_in in range(N):
            x2 = x ^ delta_in  # bitwise XOR
            sx2 = sbox[x2]
            delta_out = sx ^ sx2
            ddt[delta_in][delta_out] += 1

    return ddt


def walsh_hadamard_transform(bool_func):
    """
    Compute the Walsh–Hadamard transform of a boolean function
    bool_func(x) -> 0 or 1, for x in [0..2^n - 1].

    Returns a list W of length 2^n, where W[w] = sum_{x} (-1)^(f(x) ^ <w,x>).

    NOTE: This is naive O(2^n * 2^n) = O(4^n). For large n, it's not feasible.
    """
    N = len(bool_func)  # 2^n
    W = [0] * N
    # We'll assume N = 2^n
    # For each w in [0..N-1]
    for w in range(N):
        total = 0
        for x in range(N):
            fx = bool_func[x]
            dot_wx = bin(w & x).count("1") % 2  # parity of bitwise AND
            val = (fx ^ dot_wx) & 1
            # (-1)^(val) = +1 if val=0, -1 if val=1
            total += 1 if val == 0 else -1
        W[w] = total
    return W


def main():
    # Step 1: Read the character set (125 symbols).
    chars = read_characters("characters.txt")

    # Step 2: Build the random S-Box (permutation over 125^3).
    sbox = build_random_sbox(chars)

    # Step 3: Write the s-box to disk
    write_sbox_to_file(sbox, file_path="sbox.json")

    # (Later) read it back
    # loaded_sbox = read_sbox_from_file('sbox.json')

    # Step 4: Demonstrate how you'd compute the DDT (NOT recommended at full size).
    # ddt = compute_ddt(sbox)  # This will be huge for 125^3.

    # Step 5: Demonstrate Walsh–Hadamard for a single bit function (toy).
    # Let's pretend we only have 2^n domain (e.g., if n=8 => domain=256).
    # This is just to show how you'd do it, not for 125^3.
    n = 4  # toy example
    # Build a random toy S-box for domain=16
    toy_sbox = list(range(2**n))
    random.shuffle(toy_sbox)

    # Let's pick bit 0 of the toy_sbox as our bool_func
    bool_func = []
    for x in range(2**n):
        # Output = toy_sbox[x]
        # Take bit 0
        bit0 = toy_sbox[x] & 1
        bool_func.append(bit0)

    wht = walsh_hadamard_transform(bool_func)
    print("Toy WHT result:", wht)


if __name__ == "__main__":
    main()
