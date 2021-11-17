# Outlier Detect

**Author**: Ben Birnbaum (benjamin.birnbaum@gmail.com)

**Contributors**: Faisal Lalani (flalani@dimagi.com), Brian DeRenzi (bderenzi@dimagi.com)

This is a Python implemention of the Multinomial Model Algorithm (MMA) for outlier detection in survey responses. It works by comparing a set of answers by a particular interviewer to the set of answers by fellow responders. Based on how similar this observed distribution is to the expected, an outlier score is given to the interviewer & question pair.

For a deeper understanding of the functionality, refer to the following papers:

B. Birnbaum, B. DeRenzi, A. D. Flaxman, and N. Lesh.  Automated quality control
for mobile data collection. In DEV ’12, pages 1:1–1:10, 2012.

B. Birnbaum. Algorithmic approaches to detecting interviewer fabrication in
surveys.  Ph.D. Dissertation, Univeristy of Washington, Department of Computer
Science and Engineering, 2012.

(See http://bbirnbaum.com/publications/ for PDF versions of
these papers.)

## Data Required

The primary input for the algorithm is a csv file containing survey responses, formatted as follows:

| interviewer_id  | question_a | question_b |
| -------------   | ------------- | ------------- |
| 1  | answer_1a  | answer_1b  |
| 2  | answer_2a  | answer_2b  |
| 3  | answer_3a  | answer_3b  |

The distribution of answers from Interviewer 1 are compared to the distribution of answers from both Interviewers 2 & 3. Likewise for Interviewer 2 with the answers of 1 & 3 and for Interviewer 3 with 1 & 2.

## Usage

1. Once you've downloaded or cloned this repository, you need to first make sure the necessary libararies are installed on your machine. Optionally, you can do this by running the following commands:

```bash
python3 setup.py install
pip install -r requirements.txt
```

2. Once the proper libraries have been installed, open the repository on your code editor of choice.

3. Before proceeding, ensure that you have correctly formatted input data. You can see the previous section of what that looks like, or use the given **example_data.csv** file. If you choose to use your own personal data, there are specific variables you will have to overwrite:

```py
# The name of the input file:
DATA_FILE = 'example_data.csv'
# The questions of the survey you wish to analyze:
QUESTIONS = ['cough', 'fever']
```

4. Once the input data and the variables pertaining to it are configured, run the file:

```bash
python3 example.py
```

6. The final output should resemble the following format:

```bash
MMA outlier scores
1
Question: question_a
Score: 15
```

## Additonal Configuration

The algorithm provides some extra functionality to get more out of the results.

* If there is a specific survey response you wish to ignore, such as blanks, you can add it as an additional parameter when running the MMA algorithm:

```py
# Compute MMA outlier scores.
# The final parameter is a list of strings you want the algorithm to ignore when comparing distributions.
# In this case, the algorithm will ignore blanks.
(mma_scores, _) = outlierdetect.run_mma(data, 'interviewer_id', QUESTIONS, [' '])
```

* The algorithm can return more than just the generated score for an interviewer/question pair; the observed distribution (the interviewer's answers), the expected distribution (everyone but the interviewer's answers), and the *p*-value can also be outputted:

```py
# The following lines are commented out in the script.
# Uncomment to output these as well.
observed_frequencies = scores[interviewer][column]['observed_freq']
expected_frequencies = scores[interviewer][column]['expected_freq']
p_value = scores[interviewer][column]['p_value']

print("Observed Frequencies: %s" % observed_frequencies)
print("Expected Frequencies: %s" % expected_frequencies)
print("P-Value: %d" % p_value)
```


