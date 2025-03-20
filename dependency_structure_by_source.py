import json
import pandas as pd
import os

excel_path = "books_to_sources.xlsx"

df_mapping = pd.read_excel(excel_path)

# Converting the data into a structure that allows quick access to sources
source_mapping = {}
for _, row in df_mapping.iterrows():
    book = row["Book"].capitalize()  
    chapter = str(row["Chapter"])
    verse = str(row["Verse"])
    source = row["Source"]
    
    if book not in source_mapping:
        source_mapping[book] = {}
    if chapter not in source_mapping[book]:
        source_mapping[book][chapter] = {}

    source_mapping[book][chapter][verse] = source  # Saving the source by book, chapter and verse
    
# Create a new folder to save the files by source
output_dir = "dicta_by_source"
os.makedirs(output_dir, exist_ok=True)

json_files = {
    "Exodus": "dicta/Exodus_dicta.json",
    "Genesis": "dicta/Genesis_dicta.json",
    "Deuteronomy": "dicta/Deuteronomy_dicta.json",
    "Leviticus": "dicta/Leviticus_dicta.json",
    "Numbers": "dicta/Numbers_dicta.json"
}

# Creating a data structure that maps the verses by source
data_by_source = {}

# Going through all the books, retrieving the text
for book, json_path in json_files.items():
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            data_json = json.load(file)

        for entry in data_json:
            chapter = str(entry["chapter"])
            verse = str(entry["verse"])
            text = entry["text"]
            prediction = entry.get("prediction", None)  # Adding `prediction` if exists
            source = source_mapping.get(book, {}).get(chapter, {}).get(verse, "Unknown")

            # Saving the verse in the appropriate source file
            if source not in data_by_source:
                data_by_source[source] = []

            entry_data = {
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "text": text
            }

            if prediction:
                entry_data["prediction"] = prediction

            data_by_source[source].append(entry_data)

# Saving data to JSON files divided by source
output_files = {}
for source, entries in data_by_source.items():
    output_json_path = os.path.join(output_dir, f"dicta_{source}.json")

    with open(output_json_path, "w", encoding="utf-8") as output_file:
        json.dump(entries, output_file, ensure_ascii=False, indent=4)

    output_files[source] = output_json_path
