# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 12:27:42 2019

Some code to scramble sentences various ways:
    (1) swap adjacent words
    (2) partition words into groups of three and scramble
    (3) swap content word with word before/after it

@author: Emily Teoh
"""
import numpy as np
import pandas as pd
import os  
import re
import random
from google.cloud import texttospeech

# swap adjacent elements
def one_swap(l):
    for i in range(0,len(l)-1,2):
        l[i], l[i+1] = l[i+1], l[i]
    return l

# swap selected element with adjacent element
def three_scramble(l):
    for i in range(0,len(l)-2,3):
        arr = np.arange(3)
        np.random.shuffle(arr) 
        l[i], l[i+1], l[i+2] = l[i+arr[0]], l[i+arr[1]], l[i+arr[2]]
    return l

def swap_selected(l,i):
    if i==0:
        l[i], l[i+1] = l[i+1], l[i]
    elif i==len(l)-1:
        l[i], l[i-1] = l[i-1], l[i]
    else:
        flip = random.choice((-1, 1))
        l[i], l[i+flip] = l[i+flip], l[i]
    return l
    
# read in word2vec content/funcWords
fW = pd.read_excel(r'path-to\word2vec\funcWords.xls',header=None)
cRC = pd.read_excel(r'path-to\word2vec\conceptRowsC.xls',header=None)

funcWords = list(fW[0])
conceptRowsC = list(cRC[0])

# read in text to be modified
file_object  = open(r'path-to\text1.txt', 'r')
sentences = file_object.readlines()
output_format = ['audio','text']

# v1: swap adjacent words
punctuation = '[.?!;,~|"]'
one_swap_sentences = []
for sentence in sentences:
    punc = re.findall(punctuation,sentence)
    phrases = re.split(punctuation,sentence)
    one_swap_phrases = [' '.join(one_swap(phrase.split())) for phrase in phrases]
    s = []
    for k in range(len(one_swap_phrases)-1):
        s.append(one_swap_phrases[k]+punc[k])
    one_swap_sentences.append(' '.join(s))

# v2: swap words in groups of 3
three_scramble_sentences = []
for sentence in sentences:
    punc = re.findall(punctuation,sentence)
    phrases = re.split(punctuation,sentence)
    three_scramble_phrases = [' '.join(three_scramble(phrase.split())) for phrase in phrases if not phrase.isspace()]
    s = []
    for k in range(len(punc)):
        s.append(three_scramble_phrases[k]+punc[k])
    three_scramble_sentences.append(' '.join(s))

# v3: swap content word with word before/after it
swap_content_words = []
for sentence in sentences:
    punc = re.findall(punctuation,sentence)
    phrases = re.split(punctuation,sentence)
    s = []
    for n_p in range(len(phrases[:-1])):
        words = phrases[n_p].split()
        for i in range(len(words)):
            if not words[i].lower() in funcWords and len(words)>1:
                swap_selected(words,i) 
        s.append(' '.join(words)+punc[n_p])
    swap_content_words.append(' '.join(s))           
            
# initialise text-to-speech client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path-to\xxx.json"
client = texttospeech.TextToSpeechClient()
voice = texttospeech.types.VoiceSelectionParams(language_code='en-US',name='en-US-Wavenet-C')
audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16,speaking_rate=0.9)
    

#save to audio and text
n_sentences = 8
split_into = round(len(sentences)/n_sentences)
if 'text' in output_format:
    for i in range(split_into):
        with open('output_oneswap'+str(i+1)+'.txt','w') as out:
            for s in one_swap_sentences[i*n_sentences:i*n_sentences+n_sentences]:
                out.write(s + '\n')
        with open('output_threescram'+str(i+1)+'.txt','w') as out:
            for s in three_scramble_sentences[i*n_sentences:i*n_sentences+n_sentences]:
                out.write(s + '\n')
        with open('output_swapcont'+str(i+1)+'.txt','w') as out:
            for s in  swap_content_words[i*n_sentences:i*n_sentences+n_sentences]:
                out.write(s + '\n')
                
if 'audio' in output_format:
        for i in range(split_into):
            if os.path.exists('output_oneswap'+str(i+1)+'.wav'):
               os.remove('output_oneswap'+str(i+1)+'.wav')
            if os.path.exists('output_threescram'+str(i+1)+'.wav'):
               os.remove('output_threescram'+str(i+1)+'.wav')
            if os.path.exists('output_swapcont'+str(i+1)+'.wav'):
               os.remove('output_swapcont'+str(i+1)+'.wav')
            # Write the response to the output file.
            synthesis_input = texttospeech.types.SynthesisInput(text=' '.join(one_swap_sentences[i*n_sentences:i*n_sentences+n_sentences]))
            response = client.synthesize_speech(synthesis_input, voice, audio_config)    
            with open('output_oneswap'+str(i+1)+'.wav',mode='bx') as out:
                out.write(response.audio_content)
                print('Audio content written to file "output_oneswap'+str(i+1)+'.wav"')
            synthesis_input = texttospeech.types.SynthesisInput(text=' '.join(three_scramble_sentences[i*n_sentences:i*n_sentences+n_sentences]))
            response = client.synthesize_speech(synthesis_input, voice, audio_config)
            with open('output_threescram'+str(i+1)+'.wav',mode='bx') as out:
            # Write the response to the output file.
                out.write(response.audio_content)
                print('Audio content written to file "output_threescram'+str(i+1)+'.wav"')
            synthesis_input = texttospeech.types.SynthesisInput(text=' '.join(swap_content_words[i*n_sentences:i*n_sentences+n_sentences]))
            response = client.synthesize_speech(synthesis_input, voice, audio_config)
            with open('output_swapcont'+str(i+1)+'.wav',mode='bx') as out:
            # Write the response to the output file.
                out.write(response.audio_content)
                print('Audio content written to file "output_swapcont'+str(i+1)+'.wav"')
