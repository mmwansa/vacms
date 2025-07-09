import pandas as pd
from simple_history.utils import bulk_create_with_history

from va_explorer.va_data_management.models import Pregnancy


def build_reference_from_xlsform(xls_path):
    """Parse an XLSForm and build mapping dictionaries.

    Returns two dictionaries:
        field_map - maps question name to list_name
        choice_map - maps list_name to {name: label}
    """
    xls = pd.read_excel(xls_path, sheet_name=None)
    survey_df = xls.get("survey")
    choices_df = xls.get("choices")
    if survey_df is None or choices_df is None:
        return {}, {}

    survey_df.columns = [c.strip().lower() for c in survey_df.columns]
    choices_df.columns = [c.strip().lower() for c in choices_df.columns]

    field_map = {}
    for _, row in survey_df.iterrows():
        qtype = str(row.get("type", ""))
        name = row.get("name")
        if not name or not qtype.startswith("select"):
            continue
        list_name = qtype.split()[-1]
        field_map[name] = list_name

    choice_map = {}
    for _, row in choices_df.iterrows():
        list_name = row.get("list_name")
        name = row.get("name")
        if list_name is None or name is None:
            continue
        # use first label column available
        label_cols = [c for c in choices_df.columns if c.startswith("label")]
        label = row.get(label_cols[0]) if label_cols else row.get("label")
        if pd.isna(label):
            label = name
        choice_map.setdefault(list_name, {})[str(name)] = str(label)

    return field_map, choice_map


def apply_reference_to_dataframe(df, field_map, choice_map):
    """Replace values in df using mappings from reference tables."""
    for field, list_name in field_map.items():
        if field not in df.columns:
            continue
        mapping = choice_map.get(list_name, {})
        df[field] = df[field].apply(lambda val, m=mapping: _map_value(val, m))
    return df


def _map_value(val, mapping):
    if pd.isna(val):
        return val
    if isinstance(val, str) and " " in val:
        # multi-select values come space separated
        return ",".join(mapping.get(v, v) for v in val.split())
    return mapping.get(str(val), val)


def load_pregnancies_from_dataframe(df):
    """Create Pregnancy objects from DataFrame and save to DB."""
    model_fields = [f.name for f in Pregnancy._meta.get_fields()]
    df = df.rename(columns=lambda c: c.rsplit("-", 1)[-1])
    field_case_mapper = {f.lower(): f for f in model_fields}
    df = df.rename(columns=lambda c: field_case_mapper.get(c.lower(), c))
    common = [c for c in df.columns if c in model_fields]
    df = df[common]
    objs = [Pregnancy(**row) for row in df.to_dict(orient="records")]
    new_objs = bulk_create_with_history(objs, Pregnancy)
    return new_objs
