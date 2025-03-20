import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

files = [
    'SHEBANQ/Genesis.xml',
    'SHEBANQ/Exodus.xml',
    'SHEBANQ/Leviticus.xml',
    'SHEBANQ/Numbers.xml',
    'SHEBANQ/Deuteronomy.xml'
]

# Counter settings
word_counter = Counter()
verse_data = []  #To store data of each verse
verse_lengths_per_book = defaultdict(list)  
word_lengths_per_book = defaultdict(list)  
word_frequency_per_book = defaultdict(Counter)  


# =====================  word frequencies, verse lengths and word lengths for each book =====================

for file in files:
    tree = ET.parse(file)
    root = tree.getroot()
    book_name = file.split('/')[-1].replace('.xml', '')  

    # Finding all the verses
    for verse in root.findall('.//{http://www.tei-c.org/ns/1.0}s'):
        words = [w.text for w in verse.findall('.//{http://www.tei-c.org/ns/1.0}w') if w.text]
        verse_text = ' '.join(words)
        
        # Counter update
        word_counter.update(words)
        word_frequency_per_book[book_name].update(words)
        
        verse_data.append({
            'Book': book_name,  
            'Verse': verse_text,
            'Verse Length': len(words),
            'Unique Words Count': len(set(words))
        })
        
        # Adding the length of the verse to the book list
        verse_lengths_per_book[book_name].append(len(words))
        
        # Calculating the length of words for each verse and adding them to the list
        word_lengths_per_book[book_name].extend([len(word) for word in words])
    
# Average verse length per book
print("\nAverage verse length by book:")
for book, lengths in verse_lengths_per_book.items():
    average_length = sum(lengths) / len(lengths) if lengths else 0
    print(f"{book}: {average_length:.2f} words")

# Average word length per book
print("\nAverage word length by book:")
for book, lengths in word_lengths_per_book.items():
    average_word_length = sum(lengths) / len(lengths) if lengths else 0
    print(f"{book}: {average_word_length:.2f} characters")
print("\n")

# Saving overall word frequency as a CSV file
word_freq_df = pd.DataFrame({
    'Word': list(word_counter.keys()),
    'Frequency': list(word_counter.values())
})
word_freq_df.to_csv('statistics/word_frequencies.csv', index=False, encoding='utf-8-sig')

# Creating an Excel file for frequency of words for each book in one sheet
word_freq_combined = []

# Collecting all the words and their frequency with the name of the book as a column
for book, counter in word_frequency_per_book.items():
    for word, freq in counter.items():
        word_freq_combined.append({
            'Book': book,
            'Word': word,
            'Frequency': freq
        })


word_freq_combined_df = pd.DataFrame(word_freq_combined)

word_freq_combined_df.to_excel('statistics/word_frequencies_by_book.xlsx', index=False)    

verse_df = pd.DataFrame(verse_data)
verse_df[['Book', 'Verse', 'Verse Length']].to_csv('statistics/verse_lengths_by_book.csv', index=False, encoding='utf-8-sig')
verse_df[['Book', 'Verse', 'Unique Words Count']].to_csv('statistics/unique_words_by_book.csv', index=False, encoding='utf-8-sig')

# ===================== phrase frequencies per book =====================

def analyze_phrase_frequencies(input_excel, output_excel):
    """
    Reads the Excel file, calculates the frequency of 'Function' and 'Phrase Type' per book,
    and exports the results to a new Excel file with two sheets.
    """
    df = pd.read_excel(input_excel)

    # Calculation of frequencies of Function for each book
    function_counts = df.pivot_table(index="Book", columns="Function", aggfunc="size", fill_value=0)
    function_counts = function_counts.reset_index()

    #Calculation of frequencies of Phrase Type for each book
    phrase_type_counts = df.pivot_table(index="Book", columns="Phrase Type", aggfunc="size", fill_value=0)
    phrase_type_counts = phrase_type_counts.reset_index()

    # Saving as a excel file with two sheets
    with pd.ExcelWriter(output_excel) as writer:
        function_counts.to_excel(writer, sheet_name="Function Frequencies", index=False)
        phrase_type_counts.to_excel(writer, sheet_name="Phrase Type Frequencies", index=False)


input_excel = "clauses_structure.xlsx"
output_excel = "statistics/phrase_frequencies_by_book.xlsx"

# Running the function
analyze_phrase_frequencies(input_excel, output_excel)

# ===================== teamim tree depths per book =====================

# A function to calculate the depth of the tree for a verse
def calculate_depth(lines, start_index):
    max_depth = 0
    for i in range(start_index + 1, len(lines)):
        line = lines[i].strip('\n')
        if line.startswith('P:'):
            break  
        depth = line.count('│') + line.count('└') + line.count('├')
        if depth > max_depth:
            max_depth = depth
    return max_depth

with open('teamim-trees.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

verse_depths = []
current_book = ''
book_mapping = {
    '0': 'Genesis',
    '1': 'Exodus',
    '2': 'Leviticus',
    '3': 'Numbers',
    '4': 'Deuteronomy'
}

for i, line in enumerate(lines):
    if line.startswith('P:'):
        verse_id = line.split(': ')[1].strip()
        book_code = verse_id.split(':')[0]
        book_name = book_mapping.get(book_code, 'Unknown')
        depth = calculate_depth(lines, i)
        verse_depths.append({'Verse': verse_id, 'Book': book_name, 'Depth': depth})

verse_depths_df = pd.DataFrame(verse_depths)
verse_depths_df.to_csv('statistics/teamim_depths_by_book.csv', index=False, encoding='utf-8-sig')

# Average depth calculation for each book
average_depth_per_book = verse_depths_df.groupby('Book')['Depth'].mean().reset_index()
average_depth_per_book.columns = ['Book', 'Average Depth']

print("Average depth per book:")
print(average_depth_per_book)


# ===================== dependency structure tree depths per book =====================

book_files = {
    'dicta/Genesis_dicta.json': 'Genesis',
    'dicta/Exodus_dicta.json': 'Exodus',
    'dicta/Leviticus_dicta.json': 'Leviticus',
    'dicta/Numbers_dicta.json': 'Numbers',
    'dicta/Deuteronomy_dicta.json': 'Deuteronomy'
}

# A function to calculate the depth of the syntax tree for a verse
def compute_tree_depth(tokens):
    tree = {}
    for idx, token in enumerate(tokens):
        head_idx = token['syntax']['dep_head_idx']
        if head_idx not in tree:
            tree[head_idx] = []
        tree[head_idx].append(idx)

    def depth(node):
        if node not in tree:
            return 1
        return 1 + max(depth(child) for child in tree[node])

    return depth(-1)

# Storing the depth of verses from all books
all_verse_depths = []

# Going through all the books
for filename, book_name in book_files.items():
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        for verse in data:
            chapter = verse.get('chapter', 'Unknown')
            verse_number = verse.get('verse', 'Unknown')
            predictions = verse.get('prediction', [])

            if predictions:
                tokens = predictions[0]['tokens']
                depth = compute_tree_depth(tokens)
                all_verse_depths.append({
                    'Book': book_name,
                    'Chapter': chapter,
                    'Verse': verse_number,
                    'Depth': depth
                })

depths_df = pd.DataFrame(all_verse_depths)
depths_df.to_csv('statistics/dependency_depths_by_book.csv', index=False, encoding='utf-8-sig')

# Calculating average depth per book
average_depth_per_book = depths_df.groupby('Book')['Depth'].mean().reset_index()
average_depth_per_book.columns = ['Book', 'Average Depth']

print("\n Average dependency tree depth per book:")
print(average_depth_per_book)


# =====================  number of clauses per verse by book - by Teamim =====================

clause_counts_text = {}
book_mapping = {
    '0': 'Genesis',
    '1': 'Exodus',
    '2': 'Leviticus',
    '3': 'Numbers',
    '4': 'Deuteronomy'
}
verse_book_counts = defaultdict(list)

with open('teamim-clauses.txt', 'r', encoding='utf-8') as file:
    current_verse = None
    clause_count = 0

    for line in file:
        line = line.strip()
        
        if line.startswith("verse:"):
            if current_verse is not None:
                clause_counts_text[current_verse] = clause_count
                # Extracting the name of the book and adding the number of verses
                book_code = current_verse.split(':')[0]
                book_name = book_mapping.get(book_code, 'Unknown')
                verse_book_counts[book_name].append(clause_count)
            # Extracting the number of the verse
            current_verse = line.split(':')[1].strip()
            clause_count = 0  
        elif line.startswith("0.") or line.startswith("1."):
            clause_count += 1

    # Adding the last verse
    if current_verse is not None:
        clause_counts_text[current_verse] = clause_count
        book_code = current_verse.split(':')[0]
        book_name = book_mapping.get(book_code, 'Unknown')
        verse_book_counts[book_name].append(clause_count)

# Calculating the average number of verses per book
average_clauses_per_book_text = pd.DataFrame({
    'Book': list(verse_book_counts.keys()),
    'Average Clauses per Verse': [sum(clauses) / len(clauses) for clauses in verse_book_counts.values()]
})

print("\nAverage number of clauses per verse by book - by Teamim:")
print(average_clauses_per_book_text)

# =====================  number of clauses per verse by book - by clauses structure =====================

file_path = 'clauses_structure.xlsx'
df = pd.read_excel(file_path)

# Counting unique verses for each verse
clause_counts_excel = df.groupby('Sentence ID')['Clause ID'].nunique().reset_index()
clause_counts_excel.columns = ['Sentence ID', 'Clause Count']

# The connection of the book to each verse
clause_counts_excel = pd.merge(clause_counts_excel, df[['Sentence ID', 'Book']].drop_duplicates(), on='Sentence ID')

# Calculating the average number of verses per book
average_clauses_per_book = clause_counts_excel.groupby('Book')['Clause Count'].mean().reset_index()
average_clauses_per_book.columns = ['Book', 'Average Clauses per Verse']

print("\nAverage number of clauses per verse by book - by clauses structure:")
print(average_clauses_per_book)

# =====================  number of unique words for each book =====================

file_path = "statistics/word_frequencies_by_book.xlsx"
word_frequencies_df = pd.read_excel(file_path)

# Calculate the number of times each word appears in each book
word_counts_by_book = word_frequencies_df.groupby(['Book', 'Word']).size().reset_index(name='Word_Frequency')

# Calculate the number of distinct words in each book (not just those appearing once)
distinct_words_per_book = word_counts_by_book.groupby('Book').size().reset_index(name='Unique_Words')

# Calculate the total number of words in each book
total_words_per_book = word_frequencies_df.groupby('Book')['Frequency'].sum().reset_index(name='Total_Words')

# Merge the data together
unique_words_analysis = total_words_per_book.merge(distinct_words_per_book, on='Book', how='left')

# Calculate the percentage of unique words for each book
unique_words_analysis['Unique_Words_Percentage'] = (unique_words_analysis['Unique_Words'] / unique_words_analysis['Total_Words']) * 100

print("\nNumber of unique words:")
print(unique_words_analysis)
