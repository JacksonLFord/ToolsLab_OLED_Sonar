% =============================================================
% --- Song of Storms - Legend of Zelda: Ocarina of Time ---
% --- Key: D minor, fixed note length for simplicity ---
% =============================================================

% --- Notes needed for D minor scale ---
notes = {'D' 'E' 'F' 'G' 'A' 'Bb' 'C'};

% --- Frequencies in octave 4 ---
% D minor sits perfectly in the mid range of a small breadboard speaker
freq = [293.66 329.63 349.23 392.00 440.00 466.16 523.25];

% --- Tempo: Song of Storms is around 180 BPM, snappy and energetic ---
BPM     = 180;
Q       = 60 / BPM;    % Quarter note (~0.33s)
E       = Q / 2;       % Eighth note (~0.17s)
H       = Q * 2;       % Half note (~0.67s)
DQ      = Q * 1.5;     % Dotted quarter (~0.50s)

Samples    = 4000;
SampleRate = 1 / Samples;

% --- Melody: main loop of Song of Storms ---
Melody = {...
    'D'  'F'  'D'  ...       % Main motif (first 3 notes, very iconic)
    'D'  'F'  'D'  ...       % Repeat of motif
    'E'  'E'  ...            % Rising step
    'C'  'C'  ...            % Falling step
    'A'  ...                 % Anchor note
    'D'  'F'  'D'  ...       % Motif again
    'D'  'F'  'D'  ...       % Motif repeat
    'E'  'G'  'E'  ...       % Second phrase rising
    'C'  'C'  ...            % Falling back
    'A'  ...                 % Anchor
    'F'  'F'  'G'  'F'  'E' ... % Running melody passage
    'D'  'E'  'F'  'A'  ...  % Ascending run
    'D'  'C'  'A'  ...       % Descending resolution
    'F'  'F'  'G'  'F'  'E' ... % Running passage repeat
    'D'  'E'  'F'  'A'  ...  % Ascending run repeat
    'D'  'C'  'A'  ...       % Final resolution
};

% --- Matching lengths for each note above ---
Lengths = [...
    E    E    Q    ...       % Main motif
    E    E    Q    ...       % Repeat
    E    E    ...            % Rising
    E    E    ...            % Falling
    H    ...                 % Anchor held
    E    E    Q    ...       % Motif again
    E    E    Q    ...       % Repeat
    E    E    E    ...       % Second phrase
    E    E    ...            % Falling
    H    ...                 % Anchor held
    E    E    E    E    E    ... % Running passage
    E    E    E    DQ   ...  % Ascending run
    E    E    H    ...       % Resolution
    E    E    E    E    E    ... % Running repeat
    E    E    E    DQ   ...  % Ascending repeat
    E    E    H    ...       % Final resolution
];

% --- Build audio buffer ---
a = [];

for i = 1:numel(Melody)
    FreqIndex = strcmp(notes, Melody{i});              % Look up frequency index
    note = 0:SampleRate:Lengths(i) - SampleRate;      % Time array for this note
    a = [a sin(2*pi*freq(FreqIndex)*note)];            % Append sine wave to buffer
end

sound(a, Samples);