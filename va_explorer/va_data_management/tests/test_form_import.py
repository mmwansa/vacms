from pathlib import Path

import pandas as pd
import pytest
from django.core.management import CommandError, call_command

from va_explorer.va_data_management.models import (
    Death,
    ODKFormChoice,
    Pregnancy,
    PregnancyOutcome,
)

pytestmark = pytest.mark.django_db


def make_definition(tmpdir):
    survey = pd.DataFrame(
        {
            "type": ["select_one yesno"],
            "name": ["consent"],
            "label": ["Consent"],
        }
    )
    choices = pd.DataFrame(
        {
            "list_name": ["yesno", "yesno"],
            "name": ["1", "0"],
            "label": ["Yes", "No"],
        }
    )
    xls_path = Path(tmpdir) / "def.xlsx"
    with pd.ExcelWriter(xls_path) as writer:
        survey.to_excel(writer, sheet_name="survey", index=False)
        choices.to_excel(writer, sheet_name="choices", index=False)
    return xls_path


def make_location_definition(tmpdir):
    """Create a definition including location fields."""
    survey = pd.DataFrame(
        {
            "type": [
                "select_one yesno",
                "select_one loc",
                "select_one loc",
                "select_one loc",
                "select_one loc",
            ],
            "name": ["consent", "district", "constituency", "ward", "ea"],
            "label": ["Consent", "District", "Constituency", "Ward", "EA"],
        }
    )
    choices = pd.DataFrame(
        {
            "list_name": [
                "yesno",
                "yesno",
                "loc",
                "loc",
                "loc",
                "loc",
            ],
            "name": ["1", "0", "1", "2", "1", "2"],
            "label": [
                "Yes",
                "No",
                "Loc1",
                "Loc2",
                "Loc1",
                "Loc2",
            ],
        }
    )
    xls_path = Path(tmpdir) / "def.xlsx"
    with pd.ExcelWriter(xls_path) as writer:
        survey.to_excel(writer, sheet_name="survey", index=False)
        choices.to_excel(writer, sheet_name="choices", index=False)
    return xls_path


def test_import_definition_and_csv(tmp_path):
    definition = make_definition(tmp_path)
    call_command("load_pregnancy_definition", str(definition))
    assert ODKFormChoice.objects.count() == 2

    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    call_command("load_pregnancy_csv", str(csv_path))
    preg = Pregnancy.objects.get()
    assert preg.consent == "Yes"


def test_death_import_definition_and_csv(tmp_path):
    definition = make_definition(tmp_path)
    call_command("load_death_definition", str(definition))
    assert ODKFormChoice.objects.filter(form_name="death").count() == 2

    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    call_command("load_death_csv", str(csv_path))
    death = Death.objects.get()
    assert death.consent == "Yes"


def test_pregnancy_outcome_import_definition_and_csv(tmp_path):
    definition = make_definition(tmp_path)
    call_command("load_pregnancy_outcome_definition", str(definition))
    assert ODKFormChoice.objects.filter(form_name="pregnancy_outcome").count() == 2

    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    call_command("load_pregnancy_outcome_csv", str(csv_path))
    outcome = PregnancyOutcome.objects.get()
    assert outcome.consent == "Yes"


def test_import_without_definition(tmp_path):
    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    with pytest.raises(CommandError):
        call_command("load_pregnancy_csv", str(csv_path))


def test_death_import_without_definition(tmp_path):
    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    with pytest.raises(CommandError):
        call_command("load_death_csv", str(csv_path))


def test_pregnancy_outcome_import_without_definition(tmp_path):
    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("consent\n1\n")
    with pytest.raises(CommandError):
        call_command("load_pregnancy_outcome_csv", str(csv_path))


def test_location_fields_case_insensitive(tmp_path):
    """Values for location fields should be mapped regardless of header case."""
    definition = make_location_definition(tmp_path)
    call_command("load_pregnancy_definition", str(definition))

    # CSV uses capitalized headers which should still map correctly
    csv_path = Path(tmp_path) / "data.csv"
    csv_path.write_text("District,Constituency,Ward,EA,Consent\n1,2,1,2,1\n")
    call_command("load_pregnancy_csv", str(csv_path))
    preg = Pregnancy.objects.get()
    assert preg.district == "Loc1"
    assert preg.constituency == "Loc2"
    assert preg.ward == "Loc1"
    assert preg.ea == "Loc2"
