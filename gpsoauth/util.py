"""Utility functions."""
import binascii


def bytes_to_int(bytes_seq):
    """Convert bytes to int."""
    return int.from_bytes(bytes_seq, "big")


def int_to_bytes(num, pad_multiple=1):
    """Packs the num into a byte string 0 padded to a multiple of pad_multiple
    bytes in size. 0 means no padding whatsoever, so that packing 0 result
    in an empty string. The resulting byte string is the big-endian two's
    complement representation of the passed in long."""

    # source: http://stackoverflow.com/a/14527004/1231454

    if num == 0:
        return b"\0" * pad_multiple
    if num < 0:
        raise ValueError("Can only convert non-negative numbers.")
    result = hex(num)[2:]
    result = result.rstrip("L")
    if len(result) & 1:
        result = "0" + result
    result = binascii.unhexlify(result)
    if pad_multiple not in [0, 1]:
        filled_so_far = len(result) % pad_multiple
        if filled_so_far != 0:
            result = b"\0" * (pad_multiple - filled_so_far) + result
    return result
