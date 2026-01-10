def rotate(number, offset):
    """Circularly shift 12-digit binary numbers."""
    offset %= 12
    return ((number >> offset) | (number << (12 - offset))) & 0xFFF

def cardinality(number):
    """Compute the number of active bits in a scale number."""
    return bin(number).count('1')

def pitch_set(number):
    """Return a list of active pitch indices (0-11) for the given scale number."""
    return [i for i in range(12) if (number >> i) & 1]

def reflect(number):
    """
    Reflect 12-bit integer about the LSB (bit 0).
    Re-orders bits: 0->0, 1->11, 2->10, ..., 11->1.
    """
    res = number & 1
    for i in range(1, 12):
        if (number >> i) & 1:
            res |= (1 << (12 - i))
    return res

def intervals(number, n=None, direction='ascending'):
    """
    Return the space (number of rotations) between each active bit.
    If n is given, only return the nth interval.
    If direction is 'descending', the scale number is reflected before computing intervals.
    """
    if direction == 'descending':
        number = reflect(number)

    indices = pitch_set(number)
    if not indices:
        return [] if n is None else None
        
    count = len(indices)
    if n is not None:
        k = n % count
        if k < count - 1:
            return indices[k+1] - indices[k]
        else:
            return 12 + indices[0] - indices[-1]
            
    res = []
    for i in range(count - 1):
        res.append(indices[i+1] - indices[i])
    res.append(12 + indices[0] - indices[-1])
    return res

def interval_count(number):
    """
    Creates a 6-digit number in base 12, where digit n is equal to the number 
    of 1-bits in the bitwise AND of a scale number and itself shifted by n.
    """
    res = 0
    for i in range(1, 7):
        shifted = rotate(number, i)
        count = cardinality(number & shifted)
        res = (res * 12) + count
    return res

def num2str(val, base):
    """Converts an integer to a string of digits in the given base."""
    if val == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = []
    while val:
        res.append(digits[val % base])
        val //= base
    return "".join(res[::-1])
