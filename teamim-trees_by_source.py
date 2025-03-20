import re
import pandas as pd

book_mapping = {
    "0": "genesis",  
    "1": "exodus",  
    "2": "leviticus",  
    "3": "numbers",  
    "4": "deuteronomy"   
}

source_file = "books_to_sources.xlsx"
df_sources = pd.read_excel(source_file)

# Clearing the data from the table and converting to lowercase
df_sources = df_sources.dropna()
df_sources["Book"] = df_sources["Book"].str.strip().str.lower()
df_sources["Chapter"] = df_sources["Chapter"].astype(str).str.strip()
df_sources["Verse"] = df_sources["Verse"].astype(str).str.strip()
df_sources["Source"] = df_sources["Source"].astype(str).str.strip()

# Converting the data into an accessible structure
source_mapping = {}
for _, row in df_sources.iterrows():
    book = row["Book"]
    chapter = row["Chapter"]
    verse = row["Verse"]
    source = row["Source"]
    
    if book not in source_mapping:
        source_mapping[book] = {}
    if chapter not in source_mapping[book]:
        source_mapping[book][chapter] = {}
    
    source_mapping[book][chapter][verse] = source

input_file = "teamim-trees.txt"
output_file = "teamim-trees_by_source.txt"

# Reading the file, converting the book numbers to names, and adding the source
with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        match = re.match(r"P: (\d+):(\d+):(\d+)", line)
        if match:
            book_num, chapter, verse = match.groups()
            book_name = book_mapping.get(book_num, "unknown")  # Converting number to book
            book_name = book_name.lower()
            
            source = source_mapping.get(book_name, {}).get(chapter, {}).get(verse, "Unknown")
            
            new_line = f"source: {source}\n"
            outfile.write(new_line)
        else:
            outfile.write(line)  # If it's not a verse, write unchanged

