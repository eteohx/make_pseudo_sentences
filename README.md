# make_pseudo_sentences

Code for reading in a text file containing intact sentences and generating pseudoword and scrambled sentences 

Input format:

.txt with one sentence on each line

Output in audio (.wav) and/or text (.txt) format:

(1) Jabberwocky sentences - same syntax as original sentences but with nouns and verbs replaced by pseudowords

(2) Scrambled sentences - same words as original sentences but with syntax destroyed

(3) .txt file with pronounciation of Jabberwocky words (useful for forced alignment)


Uses gibberish module to generate pseudowords, Stanford CoreNLP for POS tagging, Google Cloud Text-to-Speech for synthesizing audio output, and g2p_en for generating pronounciation of Jabberwocky words
