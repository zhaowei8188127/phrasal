#!/usr/bin/env python
#
# Convert source side analysis to an R data frame. The source
# side analysis is generated by edu.stanford.nlp.ptm.SourceTextAnalysis.
#
#
import sys
import csv
from os import listdir,linesep
from os.path import basename,dirname
from collections import namedtuple,Counter
from argparse import ArgumentParser
from math import log,exp

import ptm_file_io

# Data frame definition
SourceData = namedtuple('SourceData', 'src_id src_len syn_complexity cnt_entity_tokens mean_lexical_freq cnt_vb cnt_nn cnt_jj cnt_adv')

def load_counts(counts_dir):
    vocab = Counter()
    n_tokens = 0
    sys.stderr.write('Loading vocabulary.')
    for i,filename in enumerate(listdir(counts_dir)):
        if ((i+1) % 10) == 0:
            sys.stderr.write('.')
        with open(counts_dir+'/'+filename) as infile:
            for line in infile:
                token,count = line.strip().split('\t')
                count = int(count)
                vocab[token] += count
                n_tokens += count
    sys.stderr.write('Done!' + linesep)
    return vocab,n_tokens

def compute_lex_freq(line, vocab, vocab_token_count):
    n_counts = 0
    for token in line:
        # Lexical frequencies are for lowercased tokens
        n_counts += vocab[token.lower()]
    lex_freq = log(n_counts) - log(len(line)*vocab_token_count)
    return exp(lex_freq)

def get_pos_count(token_data_list, pos_prefix):
    count = 0
    for token in token_data_list:
        if token.pos.startswith(pos_prefix):
            count += 1
    return count

def make_frame(token_data_file, sentence_data_file, src_filename, counts_dir):
    """ Create the data frames from the raw input files.

    Args:
    Returns:
    Raises:
    """
    sent_data = ptm_file_io.load_sentence_data(sentence_data_file)
    token_data = ptm_file_io.load_token_data(token_data_file)
    vocab,vocab_token_count = load_counts(counts_dir)

    with open(src_filename) as infile:
        csv_file = csv.writer(sys.stdout)
        write_header = True
        for i,line in enumerate(infile):
            line = line.strip().split()
            sent_i = sent_data[i]
            assert int(sent_i.src_id) == i
            tokens_i = token_data[i]
            lex_freq = compute_lex_freq(line, vocab, vocab_token_count)
            cnt_vb = get_pos_count(tokens_i, 'VB')
            cnt_nn = get_pos_count(tokens_i, 'N')
            cnt_jj = get_pos_count(tokens_i, 'JJ')
            cnt_adv = get_pos_count(tokens_i, 'RB')
            
            row = SourceData(src_id=str(i),
                             src_len=str(len(line)),
                             syn_complexity=sent_i.syn_complexity,
                             cnt_entity_tokens=sent_i.n_entity_tokens,
                             mean_lexical_freq=str(lex_freq),
                             cnt_vb=str(cnt_vb),
                             cnt_nn=str(cnt_nn),
                             cnt_jj=str(cnt_jj),
                             cnt_adv=str(cnt_adv))
            
            if write_header:
                write_header = False
                csv_file.writerow(list(row._fields))
            csv_file.writerow([x for x in row._asdict().itervalues()])

            
def main():
    desc='Make source characteristics data frame'
    parser=ArgumentParser(description=desc)
    parser.add_argument('src_file',
                        help='The (tokenized) source file.')
    parser.add_argument('token_data',
                        help='Token-level data from SourceTextAnalysis.')
    parser.add_argument('sentence_data',
                        help='Sentence level data from SourceTextAnalysis.')
    parser.add_argument('vocab_counts',
                        help='Directory counting counts files for computing lexical frequency.')
    args = parser.parse_args()

    make_frame(args.token_data, args.sentence_data,
               args.src_file, args.vocab_counts)

    
if __name__ == '__main__':
    main()
