import pytest 
import pandas as pd 
from comorbidicare.cleaning.clean_problems import clean_problems

@pytest.mark.parametrize('required_column', ["SUBJECT","PROBLEM_CODE","PROBLEM_DT_TM"])
def test_required_columns_are_present(required_column, raw_problems_df):

    problems = raw_problems_df.copy().drop(required_column, axis=1)
    with pytest.raises(ValueError, match = 'Missing required problem columns'):
        clean_problems(problems)

def test_column_names_are_normalised(raw_problems_df):
    problems = raw_problems_df.copy()
    cleaned = clean_problems(problems)

    assert {column.strip().lower() for column in problems.columns} <= set(cleaned.columns)
    assert all(column == column.lower() for column in cleaned.columns)


def test_duplicate_columns_are_detected(raw_problems_df):
    problems = raw_problems_df.copy()
    problems[" problem_code "] = problems["PROBLEM_CODE"]

    with pytest.raises(ValueError, match = 'Duplicate problem columns after normalisation'):
        clean_problems(problems)

@pytest.mark.parametrize("missing", [None,"", "none", "null", "nan", "n/a", "na"])
def test_require_subject_identifier(raw_problems_df, missing):
    problems = raw_problems_df.copy()
    problems.loc[0, "SUBJECT"] = missing

    with pytest.raises(ValueError, match = 'Problem records contain missing subject identifiers'):
        clean_problems(problems)

def test_invalid_dates_are_coerced_to_nat(raw_problems_df):
    problems = raw_problems_df.copy()
    problems.loc[0, "PROBLEM_DT_TM"] = "invalid_date"

    cleaned = clean_problems(problems)

    assert pd.isna(cleaned.loc[0, "problem_dt_tm"])

def test_missing_codes_are_dropped(raw_problems_df):
    problems = raw_problems_df.copy()
    problems.loc[0, "PROBLEM_CODE"] = None

    cleaned = clean_problems(problems)

    assert cleaned.shape[0] == problems.shape[0] - 1


@pytest.mark.parametrize("column", ["PROBLEM_CODE", "PROBLEM_DESC"])
def test_code_string_cleaning(raw_problems_df, column):
    problems = raw_problems_df.copy()
    problems.loc[0, column] = "  test  "

    cleaned = clean_problems(problems)

    assert cleaned.loc[0, column.lower()] == "test"

def test_cleaning_works_without_prob_desc(raw_problems_df):
    problems = raw_problems_df.copy().drop("PROBLEM_DESC", axis=1)

    cleaned = clean_problems(problems)

    assert "problem_desc" not in cleaned.columns


def test_dates_to_datetime(raw_problems_df):
    problems = raw_problems_df.copy()

    cleaned = clean_problems(problems)

    assert cleaned.loc[0, "problem_dt_tm"] == pd.Timestamp("2024-03-01")

def test_empty_output(raw_problems_df):
    problems = raw_problems_df.copy()
    problems.loc[:, "PROBLEM_CODE"] = None

    cleaned = clean_problems(problems)

    columns = ['subject', 'problem_code', 'problem_dt_tm']
    assert cleaned.empty
    assert all(column in cleaned.columns for column in columns)

def test_duplicate_records_are_dropped(raw_problems_df):
    problems = pd.concat([raw_problems_df, raw_problems_df], ignore_index=True)

    cleaned = clean_problems(problems)

    assert cleaned.shape[0] == raw_problems_df.shape[0]