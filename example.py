#!/usr/bin/env python
# encoding: utf-8
"""
example.py

Created by Ben Birnbaum on 2012-12-02.
benjamin.birnbaum@gmail.com

Example use of outlierdetect.py module.
"""

from __future__ import print_function
from matplotlib import mlab
import outlierdetect
import pandas as pd


DATA_FILE = 'example_data.csv'


def print_scores(scores):
    for interviewer in scores.keys():

        print("%s" % interviewer)

        for column in scores[interviewer].keys():
            
            score = scores[interviewer][column]['score']
            observed_frequencies = scores[interviewer][column]['observed_freq']
            expected_frequencies = scores[interviewer][column]['expected_freq']
            p_value = scores[interviewer][column]['p_value']

            print("Interviewer: %s" % interviewer)
            print("Question: %s" % column)
            print("Score: %d" % score)

if __name__ == '__main__':
    data = pd.read_csv(DATA_FILE)  # Uncomment to load as pandas.DataFrame.
    
    # Fill in with responses you wish to skip over.
    ignore_responses = []

    # Compute MMA outlier scores.
    (mma_scores, _) = outlierdetect.run_mma(data, 'interviewer_id', ['cough', 'fever'], ignore_responses)
    print("\nMMA outlier scores")
    print_scores(mma_scores)
