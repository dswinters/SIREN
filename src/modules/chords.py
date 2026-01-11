from .math import rotate, pitch_set

def _to_roman(interval):
    # Map chromatic interval to Roman numeral
    return ["I", "II", "II", "III", "III", "IV", "V", "V", "VI", "VI", "VII", "VII"][interval % 12]

TRIADS = {
    0b000100010001: lambda i: f"{_to_roman(i)}⁺",       # Augmented
    0b000010010001: lambda i: _to_roman(i),             # Major
    0b000010001001: lambda i: _to_roman(i).lower(),     # Minor
    0b000001001001: lambda i: f"{_to_roman(i).lower()}°" # Diminished
}

def compute_chords(scale_shape):
    """
    For each active note in the scale, find which triads can be built upon it.
    Returns a list of lists, where each inner list contains the chord shapes
    valid for that scale degree.
    """
    chords = []
    
    for degree in pitch_set(scale_shape):
        # Rotate the scale so the current degree is at 0 (the root)
        # This allows us to compare against the fixed chord shapes
        shifted_scale = rotate(scale_shape, degree)
        chords.append([chord for chord in TRIADS if (shifted_scale & chord) == chord])
        
    return chords