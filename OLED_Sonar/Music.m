% These are the notes and frequencies for the song suga suga.
notes = {'C' 'D' 'Eb' 'F' 'G' 'Ab' 'Bb'};
freq = [261.63 293.66 311.13 349.23 392.00 415.30 466.16];
% Above sets up th frequencies for each of thenotes
Melody = {...
    'F'  'F'  'Eb' 'F'  ...     % Suga suga...
    'Bb' 'Ab' 'F'  'Eb' ...     % ...how you get so fly
    'F'  'F'  'Eb' 'F'  ...     % Suga suga...
    'Ab' 'G'  'F'  'Eb' ...     % ...how you get so fly
    'F'  'F'  'Eb' 'F'  ...     % Repeat of hook
    'Bb' 'Ab' 'F'  'Eb' ...
    'F'  'Ab' 'Bb' 'Ab' ...
    'F'  'Eb' 'F'  'F'  ...
};
NoteLength = 0.3; % Each note plays for half a second (THIS IS TEMPO - If the note length changes as the song goes, you will have to have an array)
Samples    = 4000;         
SampleRate = 1/Samples;  % You are sampling a sine wave, so you are getting each part of the sin wave. Its to emulate smooth sound by taking a lot of points from a line
a = [];
for i = 1:numel(Melody) % This iterates over the list of notes and adds it to th array
    FreqIndex = strcmp(notes,Melody{i}); % This gets the index of I in the array notes
    note = 0:SampleRate:NoteLength - SampleRate; %This creates a sequence of time events where we will make sounds
    a = [a sin(2*pi*freq(FreqIndex)*note)]; %This is just sin(2πft), where the array is a bunch of "sound wave" shapes. The a[ a ] is basically a a++.           
end;
                   
sound(a,Samples);