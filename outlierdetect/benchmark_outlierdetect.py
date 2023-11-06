"""
benchmark_outlierdetect.py

Created by Anna Dixon on 2023-10-25.

Benchmark script for outlierdetect.py.  To run:

python benchmark_outlierdetect.py

"""

import timeit
import pandas as pd
import numpy as np
from datasets import load_dataset
import timeit
from line_profiler import profile
import outlierdetect

def prepare_dataset(agg_unit_scale=0.01, num_attr=3):
    """Prepares dataset for outlier detection algo benchmarking.
    Sets variables as global for easy use of benchmarking/profiling.

    Benchmark dataset is scikit-learn's Adult Census Income Dataset hosted by Hugging Face and
    originally retrieved from the UCI machine learning repository. It contains ~32.6k rows of
    anonymized income information and related factors from the 1994 Census Bureau database.
    For the pruposes of benchmarking the outlier detection algorithm, we simulate the outlier
    detection of worker surveys by randomly assigning an aggregation unit between 0 and
    agg_unit_scale*len(data), meant to represent a worker id. The outlier detection is run on
    the "education", "occupation" and "marital.status" fields of the dataset which are
    categorical variables containing 16, 15 and 7 unique values, respectively.


    Args:
        agg_unit_scale (float): Constant multiplier for aggregation unit in outlier detection.
            For example, if dataset length 10,000 and agg_unit_scale=0.01, the number of agg units
            (e.g. workers) is 100. Must be between 0 and 1.
        num_attr (int): Number of survey questions to use in benchmarking. Must be in [1,2,3].
    Returns:
        None
    """
    global data
    global agg_col
    global attributes
    data = load_dataset("scikit-learn/adult-census-income")
    data = data['train'].to_pandas()
    agg_col = 'worker_id'
    #Add a worker id column (agg unit)
    data[agg_col] = np.random.randint(round(len(data)*agg_unit_scale), size=len(data))
    attributes = ['education', 'occupation', 'marital.status'][:num_attr]
    return None

@profile
def run_sample_mma():
    """
    Runs MMA algorithm for benchmarking dataset.
    Args:
        None
    Returns:
        None
    """
    outlierdetect.run_mma(data, agg_col, attributes)
    return None

def run_line_profiler():
    prepare_dataset()
    run_sample_mma()
    return None


def run_benchmark():
    """
    Prints execution time for running outlier detection algorithm on dataset and observes
    changes in runtime for different values of number of aggregation units (e.g. number of
    workers) and number of fields/questions. Execution time is measured as the minimum of 5
    runs, with each run executing the outlier detection algorithm 4 times.

    Args:
        None
    Returns:
        None

    """
    print('Benchmarking outlier detection algorithm')
    
    print('')
    print('Observing impact of aggregation unit scale')
    for agg_unit_scale in [0.01, 0.02, 0.03]:
        min_runtime = min(timeit.repeat("run_sample_mma()", setup="prepare_dataset(agg_unit_scale={})".format(agg_unit_scale), globals=globals(), number=4))
        formatted_time = "{:.2f}".format(min_runtime)
        print(f"    Aggregation unit scale = {agg_unit_scale}, Execution time: {formatted_time} seconds")
    
    print('')
    print('Observing impact of number of questions')
    for num_attr in [1,2,3]:
        min_runtime = min(timeit.repeat("run_sample_mma()", setup="prepare_dataset(num_attr={})".format(num_attr), globals=globals(), number=4))
        formatted_time = "{:.2f}".format(min_runtime)
        print(f"    Number of questions = {num_attr}, Execution time: {formatted_time} seconds")
    return None   


if __name__ == '__main__':
    run_benchmark()
    #run_line_profiler()