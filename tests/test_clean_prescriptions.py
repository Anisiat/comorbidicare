import pytest 
import pandas as pd 
from comorbidicare.cleaning.clean_prescriptions import clean_prescriptions


def test_duplicate_columns_after_normalisation_raise(raw_prescriptions_df):
    df = raw_prescriptions_df.copy()
    df[" medication_name_short "] = df["MEDICATION_NAME_SHORT"]

    with pytest.raises(
        ValueError,
        match="Duplicate prescription columns"
    ):
        clean_prescriptions(df)

@pytest.mark.parametrize("column", [ "SUBJECT", "MEDICATION_NAME_SHORT","ORDER_DT_TM"])
def test_missing_columns(raw_prescriptions_df, column):
    """
    Test that the function raises an error when required columns are missing.
    """
    df = raw_prescriptions_df.copy()
    df = df.drop(columns=[column])  # Drop a required column

    with pytest.raises(ValueError, match="Missing required"):
        clean_prescriptions(df)

def test_usable_subject_identifier(raw_prescriptions_df, missing_value):
    """
    Test that the function raises an error when subject identifiers are missing.
    """
    df = raw_prescriptions_df.copy()
    df["SUBJECT"] = missing_value  # Set subject identifiers to None

    with pytest.raises(ValueError):
        clean_prescriptions(df)

@pytest.mark.parametrize("medication_name", ["ACLIDINIUM", "Aclidinium", '  aclidinium'])
def test_clean_medication_names(raw_prescriptions_df, medication_name):
    """
    Test that the function lowercases medication names for consistent matching.
    """
    df = raw_prescriptions_df.copy()
    df["MEDICATION_NAME_SHORT"] = medication_name
    cleaned_df = clean_prescriptions(df)

    assert all(cleaned_df["medication_name_short"] == "aclidinium")


def test_coerce_invalid_dates(raw_prescriptions_df):
    """
    Test that the function coerces invalid dates to NaT.
    """
    df = raw_prescriptions_df.copy()
    df["ORDER_DT_TM"] = ["2024-01-01", "invalid_date", "2024-03-01"]
    cleaned_df = clean_prescriptions(df)

    assert pd.isna(cleaned_df.loc[1, "order_dt_tm"])  # Check that invalid date is NaT

def test_empty_medication_name_removal(raw_prescriptions_df):
    """
    Test that the function removes rows without a medication name.
    """
    df = raw_prescriptions_df.copy()
    df.loc[1, "MEDICATION_NAME_SHORT"] = None  # Set a medication name to None
    cleaned_df = clean_prescriptions(df)

    assert cleaned_df.shape[0] == 2  # Check that the row with None is removed

def test_duplicate_rows_are_removed(raw_prescriptions_df):
    df = pd.concat(
        [raw_prescriptions_df, raw_prescriptions_df],
        ignore_index=True,
    )

    cleaned = clean_prescriptions(df)

    assert len(cleaned) == len(raw_prescriptions_df)

def test_order_dates_are_converted_to_datetime(raw_prescriptions_df):
    cleaned = clean_prescriptions(raw_prescriptions_df)

    assert pd.api.types.is_datetime64_any_dtype(
        cleaned["order_dt_tm"]
    )