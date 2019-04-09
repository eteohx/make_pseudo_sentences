# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 23:33:57 2019

Input: (Coherent) Story/Sentences

Output:
(1) Jabberwocky (syntax intact, but nouns and verbs replaced with nonsense words) sentences, and 
(2) Shuffled (same words but syntax destroyed) sentences
in text (.txt) and/or audio (.wav) form
Also outputs IPA pronounciation for jabberwocky words (for forced alignment)

Dependencies: nltk, g2p_en (+ tensorflow), stanford CoreNLP parser (+java8), 
        Google Cloud text-to-speech

@author: Emily Teoh
"""
import gibberish
import re
import os
from g2p_en import g2p
from nltk.parse import CoreNLPParser
from nltk.corpus import words
from random import choice
from math import log
from google.cloud import texttospeech
from scipy.io import wavfile
from scipy.signal import hilbert, find_peaks, butter, filtfilt

# function for shuffling to a certain percentage - set perc to between 0 and 1
def jitter(items,perc):
    n = len(items)
    m = (n**2 * log(n))
    items = items[:]
    indices = list(range(n-1))
    for i in range(int(perc*m)):
        j = choice(indices)
        items[j],items[j+1] = items[j+1],items[j]
    return items

# butterworth LP filter
fc = 8  # Cut-off frequency of the filter
all_words = words.words()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path-to//xxx.json"
client = texttospeech.TextToSpeechClient()
voice = texttospeech.types.VoiceSelectionParams(language_code='en-US',name='en-US-Wavenet-C')
audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16,speaking_rate=0.9)
    
# import text
file_object  = open(r'text1.txt', 'r')
sentences = file_object.readlines()
output_format = ['audio','text']
#maybe parse by fullstop? # 

# POS tagging
# open terminal and cd to C:\Users\emily\Documents\stanford-corenlp-full-2016-10-31
# java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
# -preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
# -status_port 9000 -port 9000 -timeout 15000 & 
pos_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='pos')
tokens = []
for n in range(len(sentences)):
    tokens.append(list(pos_tagger.tag(sentences[n].split())))

# make jabberwocky: change all verbs and nouns to gibberish
# write nonsense words to dictionary for forced alignment
pos_to_replace = ['NNP','VBD','VBZ','NNS','VB','NN','VBG','VBP','VBN']
cant_pronounce = []
jwocky_ss = []
add_to_dict = []
for i in range(len(tokens)):
    jwocky_s = []
    for j in range(len(tokens[i])):
        if tokens[i][j][1] in pos_to_replace:
            pseudo_word = 'hello'
            while pseudo_word in (all_words + cant_pronounce): #while the word is not in dictionary
                pseudo_word = gibberish.generate_word()
                if tokens[i][j][1] in ['VBG']:
                    pseudo_word = pseudo_word+'ing'
                elif tokens[i][j][1] in ['VBD']:
                    pseudo_word = pseudo_word+'ed'
                elif tokens[i][j][1] in ['NNS']:
                    pseudo_word = pseudo_word+'s'
                #make google say the word to check that it doesn't just spell it out
                synthesis_input = texttospeech.types.SynthesisInput(text=pseudo_word)
                response = client.synthesize_speech(synthesis_input, voice, audio_config)
                if os.path.exists('pseudoword.wav'):
                    os.remove('pseudoword.wav')
                with open('pseudoword.wav', mode='bx') as out:
                    # Write the response to the output file.
                    out.write(response.audio_content)
                #read wav and check that it's pronounced and not spelled out
                x = wavfile.read('pseudoword.wav', mmap=False)
                w = fc / (x[0]/ 2) # Normalize the frequency
                b, a = butter(5, w, 'low')
                output = filtfilt(b, a, abs(hilbert(x[1])))
                peaks, _ = find_peaks(output, height=0)
                # if the spell the word out, there will be a lot of peaks
                if len(peaks)>4:
                    cant_pronounce.append(pseudo_word)
            jwocky_s.append(pseudo_word)
            add_to_dict.append(''.join(pseudo_word).upper() + '\t' + ' '.join(g2p(pseudo_word)))
        else:
            jwocky_s.append(tokens[i][j][0]) 
    jwocky_ss.append(' '.join(jwocky_s))
    
with open('eng_dict_add.txt','w') as out:
    for entry in add_to_dict:
        out.write(entry + '\n')
            
# shuffle: mess up structure and parse again.. compute probability of syntax
# shuffle_degree controls the strength of shuffling
shuffle_perc = 0.1
shuffle_ss = []
punctuation = '[.?!;,~|"]'
for i in range(len(sentences)):
    punc = re.findall(punctuation,sentences[i])
    phrases = re.split(punctuation,sentences[i])
    shuffle_s = []
    for k in range(len(phrases)-1):
        shuffle_s.append(' '.join(jitter(phrases[k].split(),shuffle_perc)))
        if k<len(phrases):
            shuffle_s.append(punc[k])
    shuffle_ss.append(' '.join(shuffle_s))

# text-to-speech: can only write about a minute of speech, so split up the text into 8-sentence blocks 
split_into = round(len(shuffle_ss)/8)

if 'text' in output_format:
    for i in range(split_into):
        with open('output_scrambled'+str(i+1)+'.txt','w') as out:
            for s in shuffle_ss[i*8:i*8+8]:
                out.write(s + '\n')
        with open('output_jwocky'+str(i+1)+'.txt','w') as out:
            for s in jwocky_ss[i*8:i*8+8]:
                out.write(s + '\n')

if 'audio' in output_format:
        for i in range(split_into):
            synthesis_input = texttospeech.types.SynthesisInput(text=' '.join(shuffle_ss[i*8:i*8+8]))
            response = client.synthesize_speech(synthesis_input, voice, audio_config)
            if os.path.exists('output_scrambled'+str(i+1)+'.wav'):
               os.remove('output_scrambled'+str(i+1)+'.wav')
            if os.path.exists('output_jwocky'+str(i+1)+'.wav'):
               os.remove('output_jwocky'+str(i+1)+'.wav')
            with open('output_scrambled'+str(i+1)+'.wav',mode='bx') as out:
            # Write the response to the output file.
                out.write(response.audio_content)
                print('Audio content written to file "output_scrambled'+str(i+1)+'.wav"')
            synthesis_input = texttospeech.types.SynthesisInput(text=' '.join(jwocky_ss[i*8:i*8+8]))
            response = client.synthesize_speech(synthesis_input, voice, audio_config)
            with open('output_jwocky'+str(i+1)+'.wav',mode='bx') as out:
            # Write the response to the output file.
                out.write(response.audio_content)
                print('Audio content written to file "output_jwocky'+str(i+1)+'.wav"')
            
        
