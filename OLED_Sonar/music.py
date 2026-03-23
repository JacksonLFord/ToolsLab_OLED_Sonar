from machine import Pin, PWM
from utime import sleep

# =============================================================
# --- Buzzer Setup ---
# =============================================================
buzzer = PWM(Pin(7))                  # Passive buzzer on GP7 uses PWM to generate tones

# =============================================================
# --- Note Frequencies (Hz) - D minor scale, octave 4 ---
# =============================================================
# Each note name maps to its frequency in Hz
notes = {
    'D':  293.66,
    'E':  329.63,
    'F':  349.23,
    'G':  392.00,
    'A':  440.00,
    'Bb': 466.16,
    'C':  523.25,
}

# =============================================================
# --- Tempo Definitions ---
# =============================================================
BPM = 180                             # Song of Storms is fast and energetic
Q   = 60 / BPM                        # Quarter note duration in seconds
E   = Q / 2                           # Eighth note
H   = Q * 2                           # Half note
DQ  = Q * 1.5                         # Dotted quarter note

# =============================================================
# --- Melody and Matching Note Lengths ---
# =============================================================
# Each entry in melody matches the duration at the same index in lengths
melody = [
    'D',  'F',  'D',                  # Main motif
    'D',  'F',  'D',                  # Repeat of motif
    'E',  'E',                        # Rising step
    'C',  'C',                        # Falling step
    'A',                              # Anchor note held
    'D',  'F',  'D',                  # Motif again
    'D',  'F',  'D',                  # Repeat
    'E',  'G',  'E',                  # Second phrase rising
    'C',  'C',                        # Falling back
    'A',                              # Anchor held
    'F',  'F',  'G',  'F',  'E',     # Running melody passage
    'D',  'E',  'F',  'A',           # Ascending run
    'D',  'C',  'A',                  # Descending resolution
    'F',  'F',  'G',  'F',  'E',     # Running passage repeat
    'D',  'E',  'F',  'A',           # Ascending run repeat
    'D',  'C',  'A',                  # Final resolution
]

lengths = [
    E,  E,  Q,                        # Main motif
    E,  E,  Q,                        # Repeat
    E,  E,                            # Rising
    E,  E,                            # Falling
    H,                                # Anchor held
    E,  E,  Q,                        # Motif again
    E,  E,  Q,                        # Repeat
    E,  E,  E,                        # Second phrase
    E,  E,                            # Falling
    H,                                # Anchor held
    E,  E,  E,  E,  E,               # Running passage
    E,  E,  E,  DQ,                  # Ascending run
    E,  E,  H,                        # Resolution
    E,  E,  E,  E,  E,               # Running repeat
    E,  E,  E,  DQ,                  # Ascending repeat
    E,  E,  H,                        # Final resolution
]

# =============================================================
# --- Play Note Function ---
# =============================================================
def play_note(freq, duration):
    # Set PWM frequency to the note frequency and 50% duty cycle for clean tone
    buzzer.freq(int(freq))
    buzzer.duty_u16(32768)            # 50% duty cycle (32768 out of 65535)
    sleep(duration * 0.9)             # Play for 90% of duration to add slight gap between notes
    buzzer.duty_u16(0)                # Silence buzzer between notes
    sleep(duration * 0.1)            # 10% gap so notes dont blur together

# =============================================================
# --- Main: Play Song of Storms ---
# =============================================================
sleep(1)                              # Brief pause before starting

for i in range(len(melody)):
    note_name = melody[i]             # Get the note name string
    duration  = lengths[i]            # Get the matching duration
    freq      = notes[note_name]      # Look up frequency from dictionary
    play_note(freq, duration)         # Play it

buzzer.deinit()                       # Release PWM resource when done