"""Derive the 17 Charlson comorbidities and the CCI score from iCARE tables."""

from importlib.metadata import PackageNotFoundError, version

from .pipeline import build_comorbidity_table

try:
    # Read the version from the installed package, so it is only set in
    # pyproject.toml.
    __version__ = version("comorbidicare")
except PackageNotFoundError:  # running from source without installing
    __version__ = "unknown"

__all__ = ["build_comorbidity_table", "__version__"]
