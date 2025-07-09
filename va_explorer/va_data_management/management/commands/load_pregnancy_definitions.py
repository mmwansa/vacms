import argparse

from django.core.management.base import BaseCommand

from va_explorer.va_data_management.utils.pregnancy_loading import (
    build_reference_from_xlsform,
    save_reference_to_db,
)


class Command(BaseCommand):
    help = "Loads pregnancy ODK definition XLSForm into reference tables"

    def add_arguments(self, parser):
        parser.add_argument("xlsform", type=argparse.FileType("rb"))

    def handle(self, *args, **options):
        field_map, choice_map = build_reference_from_xlsform(options["xlsform"])
        if not field_map or not choice_map:
            self.stdout.write("No survey or choices sheet found in XLSForm")
            return
        save_reference_to_db(field_map, choice_map)
        self.stdout.write(
            f"Loaded {len(field_map)} fields and {sum(len(c) for c in choice_map.values())} choices"
        )
