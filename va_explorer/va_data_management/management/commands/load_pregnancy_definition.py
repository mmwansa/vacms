import argparse
import re
import pandas as pd
from django.core.management.base import BaseCommand
from va_explorer.va_data_management.models import ODKFormChoice

def normalize_string(s):
    """Strip whitespace, replace hyphens with underscores, remove quotes."""
    if pd.isnull(s):
        return ""
    s = str(s).strip().replace("-", "_")
    # Remove surrounding single or double quotes
    if s.startswith(("'", '"')):
        s = s[1:]
    if s.endswith(("'", '"')):
        s = s[:-1]
    return s

def normalize_value(val):
    """Normalize and remove leading zeros and .0 for integer-like values."""
    if pd.isnull(val):
        return ""
    # Handle floats that are integer-like (e.g., 1.0, 2.0)
    try:
        if isinstance(val, float) and val.is_integer():
            val = int(val)
    except Exception:
        pass
    s = normalize_string(val)
    # Also handle strings like '1.0', '02.0'
    try:
        if s.replace('.', '', 1).isdigit():
            float_val = float(s)
            if float_val.is_integer():
                s = str(int(float_val))
    except Exception:
        pass
    # Remove leading zeros for digit codes
    if s.isdigit():
        s = str(int(s))
    return s

class Command(BaseCommand):
    """Load the pregnancy ODK XLSForm definition with full normalization."""

    help = "Load pregnancy form definition (fully normalized)"

    def add_arguments(self, parser):
        parser.add_argument("definition_file", type=argparse.FileType("rb"))

    def handle(self, *args, **options):
        form_name = "pregnancy"
        definition_file = options["definition_file"]

        survey = pd.read_excel(definition_file, sheet_name="survey")
        choices = pd.read_excel(definition_file, sheet_name="choices")

        label_col = None
        for col in choices.columns:
            if str(col).lower().startswith("label"):
                label_col = col
                break
        if not label_col:
            self.stderr.write("Could not find label column in choices sheet")
            return

        created = 0
        norm_form_name = normalize_string(form_name)
        for _, srow in survey.iterrows():
            qtype = str(srow.get("type", ""))
            match = re.match(r"select_(?:one|multiple)\s+(.+)", qtype)
            if not match:
                continue
            list_name = match.group(1)
            field = srow.get("name")
            if not field:
                continue
            norm_field = normalize_string(field)
            sub = choices[choices["list_name"] == list_name]
            for _, crow in sub.iterrows():
                raw_value = crow["name"]
                raw_label = crow[label_col]
                norm_value = normalize_value(raw_value)
                norm_label = str(raw_label).strip()
                ODKFormChoice.objects.update_or_create(
                    form_name=norm_form_name,
                    field_name=norm_field,
                    value=norm_value,
                    defaults={"label": norm_label},
                )
                created += 1
        self.stdout.write(f"Loaded {created} choices for form {form_name} (fully normalized)")
