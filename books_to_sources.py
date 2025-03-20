import xml.etree.ElementTree as ET
import re
import os
import pandas as pd
import requests

# מספר פסוקים בכל פרק - מבוסס על התנ"ך המסורתי
verses_per_chapter = {
    "Genesis": {1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22, 7: 24, 8: 22, 9: 29, 10: 32,
                11: 32, 12: 20, 13: 18, 14: 24, 15: 21, 16: 16, 17: 27, 18: 33, 19: 38, 20: 18,
                21: 34, 22: 24, 23: 20, 24: 67, 25: 34, 26: 35, 27: 46, 28: 22, 29: 35, 30: 43,
                31: 55, 32: 33, 33: 20, 34: 31, 35: 29, 36: 43, 37: 36, 38: 30, 39: 23, 40: 23,
                41: 57, 42: 38, 43: 34, 44: 34, 45: 28, 46: 34, 47: 31, 48: 22, 49: 33, 50: 26},

    "Exodus": {1: 22, 2: 25, 3: 22, 4: 31, 5: 23, 6: 30, 7: 29, 8: 32, 9: 35, 10: 29,
                11: 10, 12: 51, 13: 22, 14: 31, 15: 27, 16: 36, 17: 16, 18: 27, 19: 25, 20: 26,
                21: 37, 22: 30, 23: 33, 24: 18, 25: 40, 26: 37, 27: 21, 28: 43, 29: 46, 30: 38,
                31: 18, 32: 35, 33: 23, 34: 35, 35: 35, 36: 38, 37: 29, 38: 31, 39: 43, 40: 38},

    "Leviticus": {1: 17, 2: 16, 3: 17, 4: 35, 5: 26, 6: 23, 7: 38, 8: 36, 9: 24, 10: 20,
                    11: 47, 12: 8, 13: 59, 14: 57, 15: 33, 16: 34, 17: 16, 18: 30, 19: 37, 20: 27,
                    21: 24, 22: 33, 23: 44, 24: 23, 25: 55, 26: 46, 27: 34},

    "Numbers": {1: 54, 2: 34, 3: 51, 4: 49, 5: 31, 6: 27, 7: 89, 8: 26, 9: 23, 10: 36,
                11: 35, 12: 16, 13: 33, 14: 45, 15: 41, 16: 50, 17: 28, 18: 32, 19: 22, 20: 29,
                21: 35, 22: 41, 23: 30, 24: 25, 25: 19, 26: 65, 27: 23, 28: 31, 29: 40, 30: 17,
                31: 54, 32: 42, 33: 56, 34: 29, 35: 34, 36: 13},

    "Deuteronomy": {1: 46, 2: 37, 3: 29, 4: 49, 5: 33, 6: 25, 7: 26, 8: 20, 9: 29, 10: 22,
                    11: 32, 12: 32, 13: 19, 14: 29, 15: 23, 16: 22, 17: 20, 18: 22, 19: 21, 20: 20,
                    21: 23, 22: 30, 23: 26, 24: 22, 25: 19, 26: 19, 27: 26, 28: 69, 29: 28, 30: 20,
                    31: 30, 32: 52, 33: 29, 34: 12}
}


books_info = {
    "Genesis": "https://tanach.us/DH/DHSpecification.Genesis.xml",
    "Exodus": "https://tanach.us/DH/DHSpecification.Exodus.xml",
    "Leviticus": "https://tanach.us/DH/DHSpecification.Leviticus.xml",
    "Numbers": "https://tanach.us/DH/DHSpecification.Numbers.xml",
    "Deuteronomy": "https://tanach.us/DH/DHSpecification.Deuteronomy.xml"
}

# Ensure DHS folder exists
if not os.path.exists("DHS"):
    os.makedirs("DHS")

# Function to download DH files
def download_dh_file(book, url):
    file_path = f"DHS/DHSpecification.{book}.xml"
    if not os.path.exists(file_path):  # Avoid re-downloading
        response = requests.get(url)
        with open(file_path, "wb") as f:
            f.write(response.content)
    return file_path

# Download files
file_paths = [download_dh_file(book, url) for book, url in books_info.items()]

# Function to parse verse ranges
def expand_verses(verse_range, book):
    verses = []
    
    # Ignore W (e.g., 3:2.1 -> 3:2)
    verse_range = re.sub(r'\.\d+', '', verse_range)

    # Full range (C:V - C:V)
    match = re.match(r"(\d+):(\d+)\s*-\s*(\d+):(\d+)", verse_range)
    if match:
        start_chapter, start_verse, end_chapter, end_verse = map(int, match.groups())
        for chapter in range(start_chapter, end_chapter + 1):
            start_verse_iter = start_verse if chapter == start_chapter else 1
            end_verse_iter = min(end_verse if chapter == end_chapter else 999, verses_per_chapter.get(book, {}).get(chapter, 0))
            for verse in range(start_verse_iter, end_verse_iter + 1):
                verses.append((book, chapter, verse))
        return verses

    # Range in same chapter (C:V - V)
    match = re.match(r"(\d+):(\d+)\s*-\s*(\d+)", verse_range)
    if match:
        chapter, start_verse, end_verse = map(int, match.groups())
        end_verse = min(end_verse, verses_per_chapter.get(book, {}).get(chapter, 0))
        for verse in range(start_verse, end_verse + 1):
            verses.append((book, chapter, verse))
        return verses

    # Single verse (C:V)
    match = re.match(r"(\d+):(\d+)", verse_range)
    if match:
        chapter, verse = map(int, match.groups())
        if verse <= verses_per_chapter.get(book, {}).get(chapter, 0):
            verses.append((book, chapter, verse))
        return verses

    verses.append((book, verse_range.strip()))
    return verses

# Dictionary for mapping verses to sources
verse_to_source = {}

# Process XML files
for file_path in file_paths:
    book = os.path.basename(file_path).split('.')[1]  # Extract book name

    tree = ET.parse(file_path)
    root = tree.getroot()

    for excerpt in root.findall(".//excerpt"):
        verse_range = excerpt.find("range").text.strip()
        source = excerpt.find("source").text.strip()

        verses = expand_verses(verse_range, book)
        for verse in verses:
            if verse not in verse_to_source:
                verse_to_source[verse] = source

# Sorting function
def verse_sort_key(verse_tuple):
    book_order = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    book, chapter, verse_num = verse_tuple
    book_index = book_order.index(book) if book in book_order else len(book_order)
    return (book_index, chapter, verse_num)

# Creating a DataFrame
data = []
for verse in sorted(verse_to_source.keys(), key=verse_sort_key):
    book, chapter, verse_num = verse
    source = verse_to_source[verse]
    data.append([book, chapter, verse_num, source])  

df = pd.DataFrame(data, columns=["Book", "Chapter", "Verse", "Source"])

# Save to Excel
output_file = "books_to_sources.xlsx"
df.to_excel(output_file, index=False)

print(f"File saved as {output_file}")
