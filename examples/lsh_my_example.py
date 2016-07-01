'''
Some examples for LSH
'''

from hashlib import sha1
import numpy as np
from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH
from os import listdir, path

import sys
import time


class SimilarityForFiles:
    N_FOR_SHINGL = 7

    def __init__(self, file_names, doc_dir):
        self.file_names = file_names
        self.min_hash_dict = {}
        self.doc_dir = doc_dir
        for file_name in file_names:
            self.min_hash_dict[file_name] = set(self.file_to_words('/'.join([self.doc_dir, file_name])))

        self.min_hash_dict = {k: self.min_hash_text(v) for k, v in self.min_hash_dict.iteritems()}
        #self.lsh = MinHashLSH(threshold=0)

        #for k, v in self.min_hash_dict.iteritems():
         #   self.lsh.insert(k, v)

    def find_more_then_threshold(self, threshold, curr_file_name):
        lsh = MinHashLSH(threshold)
        current_m = self.min_hash_text(set(self.file_to_words('/'.join([self.doc_dir, curr_file_name]))))
        for k, v in self.min_hash_dict.iteritems():
            lsh.insert(k, v)
        result = lsh.query(current_m)
        print("Candidates with Jaccard similarity > " + str(threshold), result)

    def show_result(self, curr_file_name):
        #current_m = self.min_hash_text(self.file_to_words('/'.join([self.doc_dir, curr_file_name])))
        current_m = self.min_hash_dict[curr_file_name]
        for k, v in self.min_hash_dict.iteritems():
            print"Estimated Jaccard for " + curr_file_name + " and " + k +" is ", current_m.jaccard(v)


    def min_hash_text(self, sm_text):
        m = MinHash()
        for d in sm_text:
            m.update(d.encode('utf8'))
        return m

    def file_to_words(self, file_name):
        with open(file_name,'r') as f:
            return self.find_ngrams(''.join(f.read().split()), self.N_FOR_SHINGL)

    def find_ngrams(self, input_list, n):
        return [''.join(x) for x in zip(*[input_list[i:] for i in range(n)])]



# print 'Number of arguments:', len(sys.argv), 'arguments.'


arg_list = str(sys.argv)
doc_dir = 'gutenberg' #arg_list[1]
curr_file = '1661.txt' #arg_list[2]

file_names = [f for f in listdir(doc_dir) if path.splitext(f)[1] == '.txt']


def find_ngrams(input_list, n):
        return [''.join(x) for x in zip(*[input_list[i:] for i in range(n)])]

if __name__ == "__main__":
    sim_for_files = SimilarityForFiles(file_names, doc_dir)
    start_time = time.time()
    sim_for_files.show_result(curr_file)
    # sim_for_files.find_more_then_threshold(0.07, curr_file)
    print("--- %s seconds ---" % (time.time() - start_time))
