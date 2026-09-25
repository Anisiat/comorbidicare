import pytest 
import pandas as pd 

from comorbidicare.cleaning.clean_diagnoses import clean_diagnoses


@pytest.fixture
def diagnoses_df():
    """ 
    Fixture to create a sample diagnoses dataframe for testing.
    """
    data = {
        'subject': [1, 2, 3],
        'spell_identifier': ['A01', 'B02', 'C03'],
        'diagnosis_date': ['2021-01-01', '2021-02-01', '2021-03-01'], 
        'diagnosis_code_icd': ['D001', 'D002', 'D003'],
        'diagnosis_code_snomed': ['S001', 'S002', 'S003'],
    }
    return pd.DataFrame(data)

@pytest.fixture
def spell_admission_dates_df():
    """
    Fixture to create a sample spell admission dates dataframe for testing.
    """
    data = {
        'subject': [1, 2, 3],
        'spell_identifier': ['A01', 'B02', 'C03'],
        'admission_date': ['2020-12-31', '2021-01-31', '2021-02-28'],
    }
    return pd.DataFrame(data)

def test_columns_are_normalised(diagnoses_df):
    """
    Test that the column names are normalised correctly.
    """
    df = diagnoses_df.rename(columns={'spell_identifier': 'SPELL_IDENTIFIER', 'diagnosis_date': 'DIAGNOSIS_DATE '})
    cleaned_df = clean_diagnoses(df)

    assert 'spell_identifier' in cleaned_df.columns
    assert 'diagnosis_date' in cleaned_df.columns
    
def test_columns_are_validated():
    """ 
    Test correct columns are validated in the input dataframe.
    """

    data = {
        'spell_identifier': ['A01', 'B02', 'C03'],
        'diagnosis_date': ['2021-01-01', '2021-02-01', '2021-03-01'], 
        'diagnosis_code_icd': ['D001', 'D002', 'D003'],
        'diagnosis_code_snomed': ['S001', 'S002', 'S003'],
    }

    df = pd.DataFrame(data)

    with pytest.raises(ValueError):
        clean_diagnoses(df)


def test_require_min_one_code_col(diagnoses_df):
    """
    Test that at least one of the code columns is required.
    """
    df = diagnoses_df.drop(columns=['diagnosis_code_icd', 'diagnosis_code_snomed'])
    
    with pytest.raises(ValueError):
        clean_diagnoses(df)


def test_missing_subject_values_are_reported():
    """
    Test that missing subject values are reported as an error.
    """
    df = pd.DataFrame({
        'subject': [1, None, 3],
        'spell_identifier': ['A01', 'B02', 'C03'],
        'diagnosis_date': ['2021-01-01', '2021-02-01', '2021-03-01'], 
        'diagnosis_code_icd': ['D001', 'D002', 'D003'],
        'diagnosis_code_snomed': ['S001', 'S002', 'S003'],
    })

    with pytest.raises(ValueError):
        clean_diagnoses(df)


def test_codes_are_cleaned(diagnoses_df):
    """
    Test that the diagnosis codes are cleaned correctly.
    """
    df = diagnoses_df.copy()
    df['diagnosis_code_icd'] = [' d001 ', 'D002', ' d0.03 ']
    df['diagnosis_code_snomed'] = ['637738 ', ' 7667 ', 'null']

    cleaned_df = clean_diagnoses(df)

    assert cleaned_df['diagnosis_code_icd'].tolist() == ['D001', 'D002', 'D003']
    assert cleaned_df['diagnosis_code_snomed'].tolist() == ['637738', '7667', pd.NA]


def test_icd_uppercase_and_dot_removal(diagnoses_df):
    """
    Test that ICD codes are converted to uppercase and dots are removed.
    """
    df = diagnoses_df.copy()
    df['diagnosis_code_icd'] = ['d001', 'D0.02', 'd0.03']

    cleaned_df = clean_diagnoses(df)

    assert cleaned_df['diagnosis_code_icd'].tolist() == ['D001', 'D002', 'D003']


def test_diagnosis_date_coercion(diagnoses_df):
    """
    Test that invalid diagnosis dates are coerced to NaT.
    """
    df = diagnoses_df.copy()
    df['diagnosis_date'] = ['2021-01-01', 'invalid_date', '2021-03-01']

    cleaned_df = clean_diagnoses(df)

    assert pd.isna(cleaned_df.loc[1, 'diagnosis_date'])


def test_spell_admission_dates_fallback(diagnoses_df, spell_admission_dates_df):
    """
    Test that spell admission dates are used as a fallback for missing diagnosis dates.
    """
    df = diagnoses_df.copy()
    df.loc[1, 'diagnosis_date'] = pd.NaT  # Set one diagnosis date to NaT

    spell_admission_dates_df = spell_admission_dates_df.copy()
    spell_admission_dates_df.loc[2, 'admission_date'] = 'invalid_date'  # Set one admission date to an invalid value
    spell_admission_dates_df.loc[2, 'spell_identifier'] = 'C03'  # Set the spell identifier for the invalid admission date
    cleaned_df = clean_diagnoses(df, spell_admission_dates_df=spell_admission_dates_df)

    assert cleaned_df.loc[1, 'comorbidity_date'] == pd.to_datetime('2021-01-31')
    assert pd.notna(cleaned_df.loc[2, 'comorbidity_date'])  # Ensure that invalid admission date does not overwrite valid diagnosis dates

    assert pd.isna(cleaned_df.loc[1, 'diagnosis_date'])
    assert cleaned_df.loc[1, 'comorbidity_date_source'] == 'spell_admission_date'
    assert cleaned_df.loc[2, 'comorbidity_date'] == pd.Timestamp('2021-03-01')
    assert cleaned_df.loc[2, 'comorbidity_date_source'] == 'diagnosis_date'

@pytest.mark.parametrize('code_column', ['diagnosis_code_icd', 'diagnosis_code_snomed'])
def test_single_coding_system_is_sufficient(code_column):
    df = pd.DataFrame({'subject': ['s1'], code_column: ['12345']})
    result = clean_diagnoses(df)
    assert len(result) == 1
    assert result['diagnosis_date'].isna().all()
    assert result['comorbidity_date'].isna().all()
    assert result['comorbidity_date_source'].isna().all()


@pytest.mark.parametrize('missing', [None, '', '  ', 'NULL', 'n/a', pd.NA])
def test_missing_subject_markers_are_rejected(diagnoses_df, missing):
    diagnoses_df['subject'] = ['s1', missing, 's3']
    with pytest.raises(ValueError, match='missing subject identifiers'):
        clean_diagnoses(diagnoses_df)


def test_fallback_requires_diagnosis_spell_identifier(diagnoses_df, spell_admission_dates_df):
    with pytest.raises(ValueError, match="must contain 'spell_identifier'"):
        clean_diagnoses(diagnoses_df.drop(columns='spell_identifier'), spell_admission_dates_df)


def test_descriptions_and_identifiers_are_cleaned(diagnoses_df):
    diagnoses_df['spell_identifier'] = [' A01 ', 'B02', ' null ']
    diagnoses_df['diagnosis_desc_icd'] = ['  Some\t description ', 'NULL', None]
    result = clean_diagnoses(diagnoses_df)
    assert result.loc[0, 'spell_identifier'] == 'A01'
    assert pd.isna(result.loc[2, 'spell_identifier'])
    assert result.loc[0, 'diagnosis_desc_icd'] == 'Some description'
    assert result['diagnosis_desc_icd'].iloc[1:].isna().all()


def test_supplied_admissions_replace_existing_dates(diagnoses_df, spell_admission_dates_df):
    diagnoses_df = diagnoses_df.drop(columns='diagnosis_date')
    diagnoses_df['admission_date'] = '1999-01-01'
    result = clean_diagnoses(diagnoses_df, spell_admission_dates_df.iloc[:2])
    assert result.loc[0, 'admission_date'] == pd.Timestamp('2020-12-31')
    assert pd.isna(result.loc[2, 'admission_date'])
    assert pd.isna(result.loc[2, 'comorbidity_date'])
    assert 'admission_date_x' not in result
    assert 'admission_date_y' not in result


def test_duplicate_admissions_after_cleaning_do_not_multiply_rows(diagnoses_df, spell_admission_dates_df):
    duplicate = spell_admission_dates_df.iloc[[0]].copy()
    duplicate['spell_identifier'] = ' A01 '
    duplicate['subject'] = ' 1 '
    result = clean_diagnoses(diagnoses_df, pd.concat([spell_admission_dates_df, duplicate]))
    assert len(result) == 3


def test_conflicting_admission_dates_are_rejected(diagnoses_df, spell_admission_dates_df):
    duplicate = spell_admission_dates_df.iloc[[0]].copy()
    duplicate['admission_date'] = '2020-12-30'
    with pytest.raises(ValueError, match='multiple records'):
        clean_diagnoses(diagnoses_df, pd.concat([spell_admission_dates_df, duplicate]))


@pytest.mark.filterwarnings("ignore:Could not infer format:UserWarning")
def test_invalid_dates_leave_date_and_source_missing(diagnoses_df, spell_admission_dates_df):
    diagnoses_df['diagnosis_date'] = 'invalid'
    spell_admission_dates_df['admission_date'] = 'invalid'
    result = clean_diagnoses(diagnoses_df, spell_admission_dates_df)
    assert result['comorbidity_date'].isna().all()
    assert result['comorbidity_date_source'].isna().all()


def test_empty_diagnoses_preserve_output_schema(diagnoses_df, spell_admission_dates_df):
    result = clean_diagnoses(diagnoses_df.iloc[:0], spell_admission_dates_df)
    assert result.empty
    assert {'subject', 'diagnosis_date', 'admission_date', 'comorbidity_date', 'comorbidity_date_source'} <= set(result.columns)

def test_duplicate_columns_error(diagnoses_df):

    diagnoses = pd.concat([diagnoses_df, diagnoses_df], axis=1)


    with pytest.raises(ValueError, match="Duplicate"):
        clean_diagnoses(diagnoses)