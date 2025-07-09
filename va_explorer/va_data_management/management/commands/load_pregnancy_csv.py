import argparse

import pandas as pd
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.utils.pregnancy_loading import (
    apply_reference_to_dataframe,
    build_reference_from_xlsform,
    load_pregnancies_from_dataframe,
)


class Command(BaseCommand):
    help = "Loads a pregnancy CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=argparse.FileType("r"))
        parser.add_argument(
            "--form-definition",
            type=str,
            required=True,
            help="Path to the XLSForm defining pregnancy choices",
        )

    def handle(self, *args, **options):
        csv_df = pd.read_csv(options["csv_file"], low_memory=False)
        form_path = options["form_definition"]

        field_map, choice_map = build_reference_from_xlsform(form_path)
        csv_df = apply_reference_to_dataframe(csv_df, field_map, choice_map)
        new_objs = load_pregnancies_from_dataframe(csv_df)
        self.stdout.write(f"Loaded {len(new_objs)} pregnancies from CSV")
