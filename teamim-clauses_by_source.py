import pandas as pd

df = pd.read_excel('books_to_sources.xlsx')

# Creating a mapping of book, chapter, verse to source
verses_mapping = {}
for index, row in df.iterrows():
    book = row['Book'].lower()  
    chapter = row['Chapter']
    verse = row['Verse']
    source = row['Source']
    verses_mapping[(book, chapter, verse)] = source

book_mapping = {
    0: 'genesis', 
    1: 'exodus', 
    2: 'leviticus', 
    3: 'numbers', 
    4: 'deuteronomy'
}

with open('teamim-clauses.txt', 'r') as file:
    lines = file.readlines()

# Creating a new file with the appropriate source
with open('teamim-clauses_by_source.txt', 'w') as file:
    for line in lines:
        if line.startswith("verse:"):
            parts = line.split(":")
            book_code = int(parts[1].strip())  # Converting the code to a number
            chapter = int(parts[2].strip())
            verse = int(parts[3].strip())
            
            # If a suitable mapping is found, inserting the source instead of the book
            book_full_name = book_mapping.get(book_code, None)
            if book_full_name:
                key = (book_full_name, chapter, verse)
                if key in verses_mapping:
                    source = verses_mapping[key]
                    line = line.replace(f"{book_code}:{chapter}:{verse}:", f"{source}:")  
                    line = line.replace("verse", "source")  # replace 'verse' with 'source'

        file.write(line)
