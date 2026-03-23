% These are the notes and frequencies for the song Never Gonna Give you Up
% by Rick Astley
notes = {'A' 'B' 'C#' 'D' 'E' 'F#' 'G#'};
freq = [440.00 493.88 554.37 587.33 659.25 739.99 830.61];
Melody = {...
    'A'  'B'  'D'  'B'  ...  % Never gonna give you up
    'F#' 'F#' 'E'  ...       % Never gonna give you up
    'A'  'B'  'D'  'B'  ...  % Never gonna let you down
    'E'  'E'  'D'  'C#' ...  % Never gonna let you down
    'A'  'B'  'D'  'B'  ...  % Never gonna run around
    'C#' 'D'  'C#' 'A'  ...  % and desert you
    'A'  'D'  'C#' 'B'  ...  % Never gonna make you cry
    'A'  'B'  'D'  'B'  ...  % Never gonna say goodbye
    'C#' 'D'  'E'  'D'  'C#' 'B' ... % Never gonna tell a lie
    'A'  'D'  'C#' ...       % and hurt you
};

NoteLength = 0.27; % Each note plays for half a second (THIS IS TEMPO - If the note length changes as the song goes, you will have to have an array)
Samples    = 4000;         
SampleRate = 1/Samples;  % You are sampling a sine wave, so you are getting each part of the sin wave. Its to emulate smooth sound by taking a lot of points from a line
a = [];
for i = 1:numel(Melody) % This iterates over the list of notes and adds it to th array
    FreqIndex = strcmp(notes,Melody{i}); % This gets the index of I in the array notes
    note = 0:SampleRate:NoteLength - SampleRate; %This creates a sequence of time events where we will make sounds
    a = [a sin(2*pi*freq(FreqIndex)*note)]; %This is just sin(2πft), where the array is a bunch of "sound wave" shapes. The a[ a ] is basically a a++.           
end;
                   
sound(a,Samples);