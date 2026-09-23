import pytest 
import pandas as pd 
from comorb_icare.cleaning.clean_problems import clean_problems

@pytest.mark.parametrize('required_column', ["SUBJECT","PROBLEM_CODE","PROBLEM_DT_TM"])
def test_required_columns_are_present(required_column, raw_problems_df):

    problems = raw_problems_df.copy().drop(required_column, axis=1)
    with pytest.raises(ValueError, match = 'Missing required problem columns'):
        clean_problems(problems)

def test_column_names_are_normalised(raw_problems_df):
    problems = raw_problems_df.copy()
    cleaned = clean_problems(problems)

    assert problems.columns[0].strip().lower() in cleaned.columns