
notes = {'C' 'D' 'E' 'F' 'G' 'A' 'B'};
freq = [261.63 293.66 329.63 349.23 392.00 440.00 493.88];
% Above sets up th frequencies for each of thenotes
Melody = {'C','D','F'};
NoteLength = 0.5; % Each note plays for half a second (THIS IS TEMPO - If the note length changes as the song goes, you will have to have an array)
Samples    = 4000;         
SampleRate = 1/Samples;  % You are sampling a sine wave, so you are getting each part of the sin wave. Its to emulate smooth sound by taking a lot of points from a line
a = [];
for i = 1:numel(Melody) % This iterates over the list of notes and adds it to th array
    FreqIndex = strcmp(notes,Melody{i}); % This gets the index of I in the array notes
    note = 0:SampleRate:NoteLength - SampleRate; %This creates a sequence of time events where we will make sounds
    a = [a sin(2*pi*freq(FreqIndex)*note)]; %This is just sin(2πft), where the array is a bunch of "sound wave" shapes. The a[ a ] is basically a a++.           
end;
                   
sound(a,Samples);