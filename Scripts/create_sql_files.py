import sys

sys.path.append("Source/FitbitExtract")
from fitbit import constants
from helper.functions import get_config_parameter


CONFIG_DIRECTORY = "config.json"
GCP_PROJECT_ID = get_config_parameter(CONFIG_DIRECTORY, "gcp_project")
BQ_DATASET = get_config_parameter(CONFIG_DIRECTORY, "gcp_bq_dataset")
TABLE_META_DATA = constants.TABLE_NAME_METADATA_MAPPING
SAVE_FILE = "Source/BigQuerySQL/create_tables.sql"
REPLACE_OBJECTS = True

# print(GCP_PROJECT_ID, BQ_DATASET)


def create_heading(name: str, suffix: str) -> str:
    name = name.upper()
    suffix = suffix.upper()
    padding = "-" * (len(name) + 9 + len(suffix))
    return f"{padding}\n--  {name} {suffix}  --\n{padding}\n"


def create_dataset_query() -> str:
    query = create_heading(BQ_DATASET, "dataset")
    query += f"\tCREATE SCHEMA IF NOT EXISTS `{GCP_PROJECT_ID}.{BQ_DATASET}`;\n\n"
    return query


def create_table_query(table_name: str, metadata: dict):
    if REPLACE_OBJECTS:
        replace_text = " OR REPLACE"
        exists_text = ""
    else:
        replace_text = ""
        exists_text = " IF NOT EXISTS"
    query = create_heading(table_name, "table")
    query += f"\tCREATE{replace_text} TABLE{exists_text} `{GCP_PROJECT_ID}.{BQ_DATASET}.{table_name}`(\n"

    for _, bq_metadata in metadata.items():
        bq_name = bq_metadata["bq_name"]
        bq_type = bq_metadata["bq_type"]
        line = f"\t\t{bq_name} {bq_type},\n"
        query += line
    query += "\t);\n\n"
    return query


def main():
    query_main = create_heading("create bigquery", "objects")
    query_main += "BEGIN \n"
    query_main += create_dataset_query()
    for table_name, metadata in TABLE_META_DATA.items():
        query_main += create_table_query(table_name, metadata)

    query_main += "END \n"
    # print(query_main)

    with open(SAVE_FILE, "w", encoding="UTF-8") as file:
        file.write(query_main)


if __name__ == "__main__":
    main()


# for field in FIELDS_METADATA:
#     new_dict = {}
#     for key, value in field.items():
#         new_dict[key] = {"bq_name": value, "bq_type": "STRING"}

#     print("Next Metadata")
#     print("")
#     print(new_dict)
#     print("")
#     print("")


# for field in FIELDS_METADATA:
#     new_dict = {}
#     for key, value in field.items():
#         new_dict[key] = value["name"]

#     print("Next Metadata")
#     print("")
#     print(new_dict)
#     print("")
#     print("")
