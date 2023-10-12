#!/usr/bin/env python
# encoding: utf-8
"""
test_outlierdetect.py

Created by Ben Birnbaum on 2012-08-27.
benjamin.birnbaum@gmail.com

Unit tests for outlierdetect.py.  To run:

python test_outlierdetect.py

You must have scipy and pandas installed for the tests to load and run.
"""

import unittest
import numpy as np
import pandas as pd

from outlierdetect import *
from outlierdetect import _get_frequencies
from outlierdetect import _STATS_AVAILABLE


def float_eq(a, b, eps=.001):
    return abs(a - b) < eps


if _STATS_AVAILABLE:
    class TestMultinomialModel(unittest.TestCase):
        def setUp(self):
            self.model = MultinomialModel()

        
        def test_compute_outlier_scores(self):
            frequencies = {
                'a' : {'y' : 12, 'n' : 23, '-' : 11},
                'b' : {'y' : 23, 'n' : 49, '-' : 39},
                'c' : {'y' : 16, 'n' : 12, '-' : 14},
            }
            outlier_scores, _, _= self.model.compute_outlier_scores(frequencies)
            self.assertEqual(sorted(outlier_scores.keys()), ['a', 'b', 'c'])
            self.assertTrue(float_eq(outlier_scores['a'], 1.3593))
            self.assertTrue(float_eq(outlier_scores['b'], 3.2995))
            self.assertTrue(float_eq(outlier_scores['c'], 3.7355))
    
    
        def test_numeric_response_values(self):
            frequencies = {
                'a' : {1 : 12, 2 : 23, 3 : 11},
                'b' : {1 : 23, 2 : 49, 3 : 39},
                'c' : {1 : 16, 2 : 12, 3 : 14},
            }
            outlier_scores, _, _ = self.model.compute_outlier_scores(frequencies)
            self.assertTrue(float_eq(outlier_scores['a'], 1.3593))
            self.assertTrue(float_eq(outlier_scores['b'], 3.2995))
            self.assertTrue(float_eq(outlier_scores['c'], 3.7355))


class TestSValueModel(unittest.TestCase):
    def setUp(self):
        self.model = SValueModel()


    def test_compute_outlier_scores(self):
        frequencies = {
            'a' : {'y' : 8,  'n' : 1,  '-' : 1},
            'b' : {'y' : 14, 'n' : 4,  '-' : 2},
            'c' : {'y' : 1,  'n' : 0,  '-' : 1},
            'd' : {'y' : 9,  'n' : 1,  '-' : 0},
            'e' : {'y' : 18, 'n' : 12, '-' : 0},
        }
        outlier_scores, _, _ = self.model.compute_outlier_scores(frequencies)
        self.assertEqual(sorted(outlier_scores.keys()), ['a', 'b', 'c', 'd', 'e'])
        self.assertTrue(float_eq(outlier_scores['a'], .333333))
        self.assertTrue(float_eq(outlier_scores['b'], .333333))
        self.assertTrue(float_eq(outlier_scores['c'], 2.333333))
        self.assertTrue(float_eq(outlier_scores['d'], 1))
        self.assertTrue(float_eq(outlier_scores['e'], 1.6666667))
    
    
    def test_numeric_response_values(self):
        frequencies = {
            'a' : {1 : 8,  2 : 1,  3 : 1},
            'b' : {1 : 14, 2 : 4,  3 : 2},
            'c' : {1 : 1,  2 : 0,  3 : 1},
            'd' : {1 : 9,  2 : 1,  3 : 0},
            'e' : {1 : 18, 2 : 12, 3 : 0},
        }
        outlier_scores, _, _ = self.model.compute_outlier_scores(frequencies)
        self.assertEqual(sorted(outlier_scores.keys()), ['a', 'b', 'c', 'd', 'e'])
        self.assertTrue(float_eq(outlier_scores['a'], .333333))
        self.assertTrue(float_eq(outlier_scores['b'], .333333))
        self.assertTrue(float_eq(outlier_scores['c'], 2.333333))
        self.assertTrue(float_eq(outlier_scores['d'], 1))
        self.assertTrue(float_eq(outlier_scores['e'], 1.6666667))


class TestGetFrequencies(unittest.TestCase):
    def setUp(self):
        self.data_rec_array = np.array([
            ('a', 'yes'),
            ('b', 'no'),
            ('a', 'yes'),
            ('a', 'yes'),
            ('b', 'no' ),
            ('a', 'no' ),
        ], dtype=[('interviewer', 'a1'), ('question', 'a3')])
        self.data_pandas = pd.DataFrame({
            'interviewer' : ['a', 'b', 'a', 'a', 'b', 'a'],
            'question'    : ['yes', 'no', 'yes', 'yes', 'no', 'no'],
        })
        self.agg_to_data = {
            'a': self.data_pandas[self.data_pandas['interviewer'] == 'a'],
            'b': self.data_pandas[self.data_pandas['interviewer'] == 'b'],
        }


    def test_get_frequencies_rec_array(self):
        freq, _ = _get_frequencies(self.data_rec_array, 'question', ['yes', 'no'], 'interviewer', 'a', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 3, 'no' : 1})
        freq, _ = _get_frequencies(self.data_rec_array, 'question', ['yes', 'no'], 'interviewer', 'b', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 0, 'no' : 2})
        freq, _ = _get_frequencies(self.data_rec_array, 'question', ['yes'], 'interviewer', 'a', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 3}
        )


    def test_get_frequencies_pandas(self):
        freq, _ = _get_frequencies(self.data_pandas, 'question', ['yes', 'no'], 'interviewer', 'a', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 3, 'no' : 1})
        freq, _ = _get_frequencies(self.data_pandas, 'question', ['yes', 'no'], 'interviewer', 'b', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 0, 'no' : 2})
        freq, _ = _get_frequencies(self.data_pandas, 'question', ['yes'], 'interviewer', 'a', self.agg_to_data)
        self.assertEqual(
            freq,
            {'yes' : 3}
        )


class TestInterfaceFunctions(unittest.TestCase):
    """Verifies that the answer given by the interface functions run_mma and run_sva is the
    same as the answer computed by the models.  Also verifies that null responses are ignored."""
    def setUp(self):
        self.data_rec_array = np.array([
            ('a', 'n', 'n', 'y'),
            ('a', 'y', 'y', 'n'),
            ('a', 'n', 'y', '-'),
            ('a', 'n', 'n', '-'),
            ('b', 'n', 'y', 'n'),
            ('b', 'n', 'n', 'y'),
            ('b', 'y', 'n', 'n'),
            ('b', 'n', 'n', 'n'),
            ('b', 'n', 'n', 'n'),
            ('b', 'y', 'n', '-'),
            ('c', 'n', 'y', '-'),
            ('c', 'y', 'y', '-'),
            ('c', 'n', 'y', 'n'),
            ('c', 'n', 'n', 'y'),
            ('c', 'y', 'n', 'y'),
            ('c', 'n', 'n', '-')
       ], dtype=[('interviewer', 'U1'), ('q1', 'U1'), ('q2', 'U1'), ('q3', 'U1')])
        self.data_pandas = pd.DataFrame.from_records(data = self.data_rec_array, columns=['interviewer', 'q1', 'q2', 'q3'])
        self.interviewers = ['a', 'b', 'c']
        self.questions = ['q1', 'q2', 'q3']
        self.frequencies = {
            'q1' : {
                'a' : {'y' : 1, 'n' : 3},
                'b' : {'y' : 2, 'n' : 4},
                'c' : {'y' : 2, 'n' : 4},                
            },
            'q2' : {
                'a' : {'y' : 2, 'n' : 2},
                'b' : {'y' : 1, 'n' : 5},
                'c' : {'y' : 3, 'n' : 3},                
            },
            'q3' : {
                'a' : {'y' : 1, 'n' : 1},
                'b' : {'y' : 1, 'n' : 4},
                'c' : {'y' : 2, 'n' : 1},                
            }
        }
        self.null_responses = ['-']


    def _test_function_using_model(self, f, model, data):
        outlier_scores, _ = f(data, 'interviewer', ['q1', 'q2'])
        q1_scores, _, _ = model.compute_outlier_scores(self.frequencies['q1'])
        q2_scores, _, _ = model.compute_outlier_scores(self.frequencies['q2'])
        for interviewer in ['a', 'b', 'c']:
            self.assertEqual(outlier_scores[interviewer]['q1']['score'], q1_scores[interviewer])
            self.assertEqual(outlier_scores[interviewer]['q2']['score'], q2_scores[interviewer])


    if _STATS_AVAILABLE:
        def test_run_mma(self):
            self._test_function_using_model(run_mma, MultinomialModel(), self.data_rec_array)
            self._test_function_using_model(run_mma, MultinomialModel(), self.data_pandas)


    def test_run_sva(self):
        self._test_function_using_model(run_sva, SValueModel(), self.data_rec_array)
        self._test_function_using_model(run_sva, SValueModel(), self.data_pandas)


    def test_works_when_some_interviewers_are_missing_values(self):    
        run_sva(self.data_rec_array[2:], 'interviewer', ['q1'])
        run_sva(self.data_pandas[2:], 'interviewer', ['q1'])
        if _STATS_AVAILABLE:
            run_mma(self.data_rec_array[2:], 'interviewer', ['q1'])
            run_mma(self.data_pandas[2:], 'interviewer', ['q1'])


if __name__ == '__main__':
    unittest.main()
