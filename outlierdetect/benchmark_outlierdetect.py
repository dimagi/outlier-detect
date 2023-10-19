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

def prepare_dataset():
    """Prepares dataset for outlier detection algo benchmarking.
    Sets variables as global for easy use of benchmarking/profiling.    
    Args:
        None

    Returns:
        None
    """
    global data
    global agg_col
    global attributes
    data = load_dataset("scikit-learn/adult-census-income")
    data = data['train'].to_pandas()
    agg_col = 'worker_id'
    #Add a worker id column
    data[agg_col] = np.random.randint(round(len(data)/100), size=len(data))
    attributes = ['education', 'occupation', 'marital.status']
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


if __name__ == '__main__':
    min_runtime = min(timeit.repeat("run_sample_mma()", setup="prepare_dataset()", globals=globals(), number=4))
    formatted_time = "{:.2f}".format(min_runtime)
    print(f"Execution time: {formatted_time} seconds")