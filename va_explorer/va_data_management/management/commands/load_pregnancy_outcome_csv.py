import argparse
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from va_explorer.va_data_management.models import ODKFormChoice, PregnancyOutcome
from va_explorer.va_data_management.utils.loading import normalize_dataframe_columns, normalize_string, normalize_value


class Command(BaseCommand):
    """Load a pregnancy outcome CSV using the previously loaded ODK definition."""

    help = "Load pregnancy outcome CSV data"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        form_name = "pregnancy_outcome"
        csv_file = options["csv_file"]

        norm_form_name = normalize_string(form_name)

        if not ODKFormChoice.objects.filter(form_name=norm_form_name).exists():
            raise CommandError("Definition for form 'pregnancy-outcome' has not been loaded")

        df = pd.read_csv(csv_file)
        df = normalize_dataframe_columns(df, PregnancyOutcome)

        odk_map_columns = [
            'province','district','constituency','ward','ea','supervisor','enumerator','consent',
            'PO_07','PO_09','PO_11','PO_11A','PO_15','PO_21','PO_22','PO_26','PO_28','PO_30',
            'PO_31','informant','PO_34','PO_35','PO_37','PO_42','PO_43','PO_44','PO_45',
            'PO_46','PO_47B','PO_48','PO_49C', 'PO_49E','PO_50'
        ]
        
        odk_map_columns = [c.strip() for c in odk_map_columns]

        # Build odk_map (all normalized but case preserved)
        all_choices = ODKFormChoice.objects.filter(form_name=norm_form_name)
        odk_map = {}
        for choice in all_choices:
            field_name = normalize_string(choice.field_name)
            value = normalize_value(choice.value)
            if field_name not in odk_map:
                odk_map[field_name] = {}
            odk_map[field_name][value] = choice.label

        def lookup_label(col, v):
            """Map value to label with normalization and robust handling."""
            v_norm = normalize_value(v)
            if v_norm in odk_map.get(col, {}):
                return odk_map[col][v_norm]
            # Fallback
            return v if pd.isnull(v) or str(v).lower() == "nan" else v_norm

        # Perform label replacement
        for col in odk_map_columns:
            if col in df.columns and col in odk_map:
                print(f"Mapping csv column '{col}' with odk_map keys {list(odk_map[col].keys())}")
                print("BEFORE:", df[col].unique())
                df[col] = df[col].map(lambda v, c=col: lookup_label(c, v))
                print("AFTER:", df[col].unique())
            elif col not in df.columns:
                print(f"Column '{col}' not in DataFrame")
            elif col not in odk_map:
                print(f"Column '{col}' not in odk_map") 

        # Remove duplicate columns after renaming
        df = df.loc[:, ~df.columns.duplicated()]

        # Only keep columns that are model fields
        model_fields = {f.name for f in PregnancyOutcome._meta.get_fields()}
        df = df[[col for col in df.columns if col in model_fields]]

        # Identify integer fields in the model
        int_fields = [
            f.name for f in PregnancyOutcome._meta.get_fields()
            if getattr(f, "get_internal_type", lambda: None)() in [
                "IntegerField",
                "BigIntegerField",
                "SmallIntegerField",
                "PositiveIntegerField",
                "PositiveSmallIntegerField",
            ]
        ]

        def nan_to_none_for_intfields(row, int_fields):
            return {
                k: (None if (k in int_fields and pd.isnull(v)) else v)
                for k, v in row.items()
            }

        objects = [
            PregnancyOutcome(**nan_to_none_for_intfields(row, int_fields))
            for row in df.to_dict(orient="records")
        ]
        PregnancyOutcome.objects.bulk_create(objects)

        self.stdout.write(f"Imported {len(objects)} records for pregnancy outcome")
