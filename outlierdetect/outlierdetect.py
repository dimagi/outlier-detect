#!/usr/bin/env python
# encoding: utf-8
# Copyright 2012 Benjamin Birnbaum
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except 
# in compliance with the License.  You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.  See the License for the specific language governing permissions and limitations
# under the License.
"""
outlierdetect.py
Updated 2013-07 by Brian DeRenzi (bderenzi@gmail.com)

Changes: 
- Optimized!

Created 2012-08-27 by Ben Birnbaum (benjamin.birnbaum@gmail.com)

This module provides functions that implement the Multinomial Model Algorithm (MMA) and the s-Value
Algorithm (SVA), as described in

B. Birnbaum, B. DeRenzi, A. D. Flaxman, and N. Lesh.  Automated quality control for mobile data
collection. In DEV '12, pages 1:1-1:10, 2012.

B. Birnbaum. Algorithmic approaches to detecting interviewer fabrication in surveys.  Ph.D.
Dissertation, Univeristy of Washington, Department of Computer Science and Engineering, 2012.

(See http://homes.cs.washington.edu/~birnbaum/pubs.html for PDF versions of these papers.)

This module is designed to work for two Python data structures: numpy.recarray and
pandas.DataFrame.  Both of these data structures consist of rows of structured data, where
columns can be accessed by string identifiers.  One of these columns must be a special column,
which is called the "aggreagation unit" column.  Each entry in this column is an identifier
which an outlier score can be computed.  For example, if the data is from a survey, the aggregation
column might be the column that lists which interviewer performed the survey; then we would be
interested in obtaining outlier scores for the interviewers.  In other situations, the aggregation
column might be different.  It just depends on what you want to compute outlier scores for.

Note that the MMA and SVA algorithms work only for categorical data.  You must specify which
categorical columns you want to compute outlier scores for.

This module requires numpy, and the implementation of MMA requires scipy.  (The module will load
without scipy, but MMA will not be available.)

The algorithms should be called by the public methods run_mma() and run_sva().


Examples:

# With pandas.DataFrame:
import pandas as pd
import outlierdetect
data = pd.read_csv('survey_data.csv')
sva_scores = outlierdetect.run_sva(data, 'interviewer_id', ['available', 'cough', 'fever'])

# With numpy.recarray:
from matplotlib import mlab
import outlierdetect
data = mlab.csv2rec('survey_data.csv')
sva_scores = outlierdetect.run_sva(data, 'interviewer_id', ['available', 'cough', 'fever'])
"""

import collections
import itertools
import numpy as np
import sys
from line_profiler import profile

# Import optional dependencies
_PANDAS_AVAILABLE = False
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    pass
_STATS_AVAILABLE = False
try:
    from scipy import stats
    _STATS_AVAILABLE = True
except ImportError:
    sys.stderr.write('Cannot import scipy.  Some models may not be available.\n')
    sys.stderr.flush()
    pass

_FLOAT_EQ_DELTA = 0.000001  # For comparing float equality

############################################## Models ##############################################
#
# Models define the core logic for computing an outlier score for a given algorithm.  Each model
# must implement a compute_outlier_scores() method defining this logic.


if _STATS_AVAILABLE:
    class MultinomialModel:
        """Model implementing MMA.  Requries scipy module."""

        @profile
        def compute_outlier_scores(self, frequencies):
            """Computes the SVA outlier scores fo the given frequencies dictionary.

            Args:
                frequencies: dictionary of dictionaries, mapping (aggregation unit) -> (value) ->
                    (number of times aggregation unit reported value).

            Returns:
                - dictionary mapping (aggregation unit) -> (MMA outlier score for aggregation unit).
                - dictionary mapping (aggregation unit) -> (number of times all aggregation units apart from agg_unit reported this value).
                - dictionary mapping (aggregation unit) -> (P value for aggregation unit).
            """
            if len(frequencies.keys()) < 2:
                raise Exception("There must be at least 2 aggregation units. " + str(frequencies.keys()))
            rng = frequencies[list(frequencies.keys())[0]].keys()
            outlier_scores = {}
            expected_frequencies = {}
            p_values = {}
            #Find the total sums for all agg units
            summed_freq = self._sum_frequencies(rng, frequencies)
            for agg_unit in list(frequencies.keys()):
                expected_frequencies[agg_unit] = summed_freq.copy()
                for r in rng:
                    expected_frequencies[agg_unit][r] -= frequencies[agg_unit][r]
                if(sum(expected_frequencies[agg_unit].values()) == 0):
                    outlier_scores[agg_unit] = 0
                    p_values[agg_unit] = 1
                else:
                    expected_counts = _normalize_counts(
                        expected_frequencies[agg_unit],
                        val=sum([frequencies[agg_unit][r] for r in rng]))
                    x2, p_value = self._compute_x2_statistic(expected_counts, frequencies[agg_unit])
                    # logsf gives the log of the survival function (1 - cdf).
                    outlier_scores[agg_unit] = -stats.chi2.logsf(x2, len(rng) - 1)
                    p_values[agg_unit] = p_value
            return outlier_scores, expected_frequencies, p_values

        @profile
        def _compute_x2_statistic(self, expected, actual):
            """Computes the X^2 statistic for observed frequencies.
            Args:
                expected: a dictionary giving the expected frequencies, e.g.,
                    {'y' : 13.2, 'n' : 17.2}
                actual: a dictionary in the same format as the expected dictionary
                    (with the same range) giving the actual distribution.

            Returns:
                the X^2 statistic for the actual frequencies, given the expected frequencies, and the p-value of the result.
            """
            rng = expected.keys()
            if actual.keys() != rng:
                raise Exception("Ranges of two frequencies are not equal.")
            num_observations = sum([actual[r] for r in rng])
            if abs(num_observations - sum([expected[r] for r in rng])) > _FLOAT_EQ_DELTA:
                raise Exception("Frequencies must sum to the same value.")
            chi_squared_stat = sum([(actual[r] - expected[r])**2 / max(float(expected[r]), 1.0)
                for r in rng])
            p_value = 1 - stats.chi2.cdf(x=chi_squared_stat,  # Find the p-value
                                df=len(rng))
            return chi_squared_stat, p_value

        @profile
        def _sum_frequencies(self, rng, frequencies):
            """Sums frequencies for each aggregation unit.
            
            Args:
                rng: all possible values to count.
                frequencies: dictionary of dictionaries, mapping (aggregation unit) -> (value) ->
                    (number of times aggregation unit reported value).
            
            Returns:
                a dictionary mapping (value) -> (number of times all aggregation units apart from
                agg_unit reported this value)

            """
            # Assumes that the range is the same for each aggregation unit in this distribution.
            # Bad things may happen if this is not the case.
            all_frequencies = {}
            for r in rng:
                all_frequencies[r] = 0
            for agg_unit in list(frequencies.keys()):
                for r in rng:
                    all_frequencies[r] += frequencies[agg_unit][r]        
            return all_frequencies


class SValueModel:
    """Model implementing SVA."""


    def compute_outlier_scores(self, frequencies):
        """Computes the SVA outlier scores fo the given frequencies dictionary.
        
        Args:
            frequencies: dictionary of dictionaries, mapping (aggregation unit) -> (value) ->
                (number of times aggregation unit reported value).
            
        Returns:
            - dictionary mapping (aggregation unit) -> (SVA outlier score for aggregation unit).
            - dictionary mapping (aggregation unit) ->  return from _normalize_counts: (a dictionary mapping (value) -> (normalized number of times all aggregation units apart from agg_unit reported this value)).
            - dictionary mapping (aggregation unit) -> (P value for aggregation unit), set to None for now and included here for consistent interface among the two models.
        """
        if (len(frequencies.keys()) < 2):
            raise Exception("There must be at least 2 aggregation units.")
        outlier_values = {}
        rng = frequencies[list(frequencies.keys())[0]].keys()
        normalized_frequencies = {}
        p_values = {}
        for j in list(frequencies.keys()):
            # If j doesn't have any answers for given question, remove j and
            # assign outlier score of 0.
            if (sum(frequencies[j].values()) == 0):
                del frequencies[j]
                outlier_values[j] = 0
                continue
            normalized_frequencies[j] = _normalize_counts(frequencies[j])
        medians = {}    
        for r in rng:
            medians[r] = np.median([normalized_frequencies[j][r]
                for j in list(normalized_frequencies.keys())])
        for j in list(frequencies.keys()):
            outlier_values[j] = 0
            for r in rng:
                outlier_values[j] += abs(normalized_frequencies[j][r] - medians[r])
        for j in list(frequencies.keys()):
            p_values[j] = None
        return self._normalize(outlier_values), normalized_frequencies, p_values
    
    
    def _normalize(self, value_dict):
        """Divides everything in value_dict by the median of values.

        If the median is less than 1 / (# of aggregation units), it divides everything by
        (# of aggregation units) instead.
        
        Args:
            value_dict: dictionary of the form (aggregation unit) -> (value).
        Returns:
            dictionary of the same form as value_dict, where the values are normalized as described
            above.
        """
        median = np.median([value_dict[i] for i in list(value_dict.keys())])
        n = len(value_dict.keys())
        if median < 1.0 / float(n):
            divisor = 1.0 / float(n)
        else:
            divisor = median
        return_dict = {}
        for i in list(value_dict.keys()):
            return_dict[i] = float(value_dict[i]) / float(divisor)
        return return_dict


########################################## Helper functions ########################################
@profile
def _normalize_counts(counts, val=1):
    """Normalizes a dictionary of counts, such as those returned by _get_frequencies().

    Args:
        counts: a dictionary mapping value -> count.
        val: the number the counts should add up to.

    Returns:
        dictionary of the same form as counts, except where the counts have been normalized to sum
        to val.
    """
    n = sum(counts.values())
    frequencies = {}
    for r in list(counts.keys()):
        frequencies[r] = val * float(counts[r]) / float(n)
    return frequencies

@profile
def _get_frequencies(data, col, col_vals, agg_col, agg_unit, agg_to_data):
    """Computes a frequencies dictionary for a given column and aggregation unit.
    
    Args:
        data: numpy.recarray or pandas.DataFrame containing the data.
        col: name of column to compute frequencies for.
        col_vals: a list giving the range of possible values in the column.
        agg_col: string giving the name of the aggregation unit column for the data.
        agg_unit: string giving the aggregation unit to compute frequencies for.
        agg_to_data: a dictionary of aggregation values pointing to subsets of data
    Returns:
        A dictionary that maps (column value) -> (number of times agg_unit has column value in
        data).
    """
    interesting_data = None
    frequencies = {}
    for col_val in col_vals:
        frequencies[col_val] = 0
        # We can't just use collections.Counter() because frequencies.keys() is used to determine
        # the range of possible values in other functions.
    interesting_data = agg_to_data[agg_unit][col]
    for name in interesting_data:
        if name in frequencies:
            frequencies[name] = frequencies[name] + 1
    return frequencies, interesting_data

@profile
def _run_alg(data, agg_col, cat_cols, model, null_responses):
    """Runs an outlier detection algorithm, taking the model to use as input.
    
    Args:
        data: numpy.recarray or pandas.DataFrame containing the data.
        agg_col: string giving the name of aggregation unit column.
        cat_cols: list of the categorical column names for which outlier values should be computed.
        model: object implementing a compute_outlier_scores() method as described in the comments
            in the models section.
        null_responses: list of strings that should be considered to be null responses, i.e.,
            responses that will not be included in the frequency counts for a column.  This can
            be useful if, for example, there are response values that mean a question has been
            skipped.
    
    Returns:
        A dictionary of dictionaries, mapping (aggregation unit) -> (column name) ->
        (outlier score).
    """
    agg_units = sorted(set(data[agg_col]), key=lambda x: (str(type(x)), x))
    outlier_scores = collections.defaultdict(dict)
    agg_to_data = {}
    agg_col_to_data = {}
    #If data is a df, use groupby for more efficient run
    if isinstance(data, pd.DataFrame):
        grouped_data = data.groupby(agg_col)
        agg_to_data = {agg_unit: group for agg_unit, group in grouped_data}
    else:
        for agg_unit in agg_units:
            agg_to_data[agg_unit] = data[data[agg_col] == agg_unit]
    agg_col_to_data = {agg_unit:{} for agg_unit in agg_units}

        
    for col in cat_cols:
        col_vals = sorted(set(data[col]), key=lambda x: (str(type(x)), x))
        col_vals = [c for c in col_vals if c not in null_responses]
        frequencies = {}
        for agg_unit in agg_units:
            frequencies[agg_unit],grouped = _get_frequencies(data, col, col_vals, agg_col, agg_unit, agg_to_data)
            agg_col_to_data[agg_unit][col] = grouped
        outlier_scores_for_col, expected_frequencies_for_col, p_values_for_col = model.compute_outlier_scores(frequencies)
        for agg_unit in agg_units:
            outlier_scores[agg_unit][col] = {'score': outlier_scores_for_col[agg_unit],
                                             'observed_freq': frequencies[agg_unit],
                                             'expected_freq': expected_frequencies_for_col[agg_unit],
                                             'p_value': p_values_for_col[agg_unit]}
    return outlier_scores, agg_col_to_data


########################################## Public functions ########################################

if _STATS_AVAILABLE:
    @profile
    def run_mma(data, aggregation_column, categorical_columns, null_responses=[]):
        """Runs the MMA algorithm (requires scipy module).
        
        Args:
            data: numpy.recarray or pandas.DataFrame containing the data.
            aggregation_column: a string giving the name of aggregation unit column.
            categorical_columns: a list of the categorical column names for which outlier values
                should be computed.
            null_responses: list of strings that should be considered to be null responses, i.e.,
                responses that will not be included in the frequency counts for a column.  This can
                be useful if, for example, there are response values that mean a question has been
                skipped.
        
        Returns:
            A dictionary of dictionaries, mapping (aggregation unit) -> (column name) ->
            ({mma outlier score, observed frequencies, expected frequencies}).
        """
        return _run_alg(data,
                        aggregation_column,
                        categorical_columns,
                        MultinomialModel(),
                        null_responses)

def run_sva(data, aggregation_column, categorical_columns, null_responses=[]):
    """Runs the SVA algorithm.
        
    Args:
        data: numpy.recarray or pandas.DataFrame containing the data.
        aggregation_column: a string giving the name of aggregation unit column.
        categorical_columns: a list of the categorical column names for which outlier values
            should be computed.
        null_responses: list of strings that should be considered to be null responses, i.e.,
            responses that will not be included in the frequency counts for a column.  This can
            be useful if, for example, there are response values that mean a question has been
            skipped.
        
    Returns:
        A dictionary of dictionaries, mapping (aggregation unit) -> (column name) ->
        ({sva outlier score, observed frequencies, expected frequencies}.
    """
    return _run_alg(data,
                    aggregation_column,
                    categorical_columns,
                    SValueModel(),
                    null_responses)
