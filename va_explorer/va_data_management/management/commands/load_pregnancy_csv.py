import argparse

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from va_explorer.va_data_management.utils.pregnancy_loading import (
    apply_reference_to_dataframe,
    load_pregnancies_from_dataframe,
    load_reference_from_db,
)


class Command(BaseCommand):
    help = "Loads a pregnancy CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        csv_df = pd.read_csv(options["csv_file"], low_memory=False)

        field_map, choice_map = load_reference_from_db()
        if not field_map or not choice_map:
            raise CommandError(
                "Pregnancy definitions have not been loaded. "
                "Run load_pregnancy_definitions first."
            )

        csv_df = apply_reference_to_dataframe(csv_df, field_map, choice_map)
        new_objs = load_pregnancies_from_dataframe(csv_df)
        self.stdout.write(f"Loaded {len(new_objs)} pregnancies from CSV")
