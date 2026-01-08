def rotate(val, offset):
    """Circularly shift 12-digit binary numbers."""
    offset %= 12
    return ((val >> offset) | (val << (12 - offset))) & 0xFFF

def cardinality(val):
    """Compute the number of active bits in a scale value."""
    return bin(val).count('1')

def reflect(val):
    """
    Reflect 12-bit integer about the LSB (bit 0).
    Re-orders bits: 0->0, 1->11, 2->10, ..., 11->1.
    """
    res = val & 1
    for i in range(1, 12):
        if (val >> i) & 1:
            res |= (1 << (12 - i))
    return res

def intervals(scale, n=None, direction='ascending'):
    """
    Return the space (number of rotations) between each active bit.
    If n is given, only return the nth interval.
    If direction is 'descending', the scale is reflected before computing intervals.
    """
    if direction == 'descending':
        scale = reflect(scale)

    indices = [i for i in range(12) if (scale >> i) & 1]
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
