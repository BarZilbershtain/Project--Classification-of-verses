import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict
import json
import os

# =====================  word frequencies, verse lengths and word lengths for each source =====================

class BibleTextAnalyzer:
    def __init__(self, excel_path, xml_files):
        self.df = pd.read_excel(excel_path)
        self.verse_to_source = self._create_verse_mapping()
        self.xml_files = xml_files

    def _create_verse_mapping(self):
        # Creates a mapping between verses and sources from the Excel file
        verse_mapping = {}
        for _, row in self.df.iterrows():
            key = (row["Book"].lower(), row["Chapter"], row["Verse"])  # יצירת מפתח אחיד
            verse_mapping[key] = row["Source"]
        return verse_mapping

    def extract_data(self):
        # Outputs both word frequency and verse lengths according to source
        word_frequencies_by_source = defaultdict(lambda: defaultdict(int))
        verse_length_data = []
        word_length_data = []  

        for book, path in self.xml_files.items():
            words_with_sources, verse_lengths = self._extract_from_xml(path, book)
            
            # Adding word frequencies by source
            for source, word in words_with_sources:
                word_frequencies_by_source[source][word] += 1
            
            # Adding verse lengths
            verse_length_data.extend(verse_lengths)
            
            # Adding word lengths
            for source, word in words_with_sources:
                word_length_data.append((source, len(word)))  

        self.word_freq_source_df = pd.DataFrame(
            [(source, word, count) for source, freq_dict in word_frequencies_by_source.items() for word, count in freq_dict.items()],
            columns=["Source", "Word", "Count"]
        )

        self.verse_length_df = pd.DataFrame(
            verse_length_data, columns=["Source", "Book", "Chapter", "Verse", "Word Count"]
        )

        # Calculating average verse lengths by source
        self.average_verse_lengths = self.verse_length_df.groupby("Source")["Word Count"].mean().reset_index()

        # Calculating average word lengths by source
        self.average_word_lengths = pd.DataFrame(word_length_data, columns=["Source", "Word Length"])
        self.average_word_lengths = self.average_word_lengths.groupby("Source")["Word Length"].mean().reset_index()

        print("\n Average verse lengths by source:")
        print(self.average_verse_lengths)

        print("\n Average word lengths by source:")
        print(self.average_word_lengths)

    def _extract_from_xml(self, file_path, book_name):
        # Reads an XML file and extracts words + verse lengths by source
        words_with_source = []
        verse_lengths = []
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}  # שמות מתחם

        for verse in root.findall(".//tei:s", ns):
            verse_id = verse.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")
            parts = verse_id.split(".")
            if len(parts) >= 4:
                chapter = int(parts[-2])
                verse_num = int(parts[-1])
                key = (book_name.lower(), chapter, verse_num)

                # Getting the source from the mapping
                source = self.verse_to_source.get(key, "Unknown")

                # Calculation of the number of words in a verse
                word_count = len(verse.findall("tei:w", ns))
                verse_lengths.append((source, book_name, chapter, verse_num, word_count))

                # Extracting words and mapping them to the source
                for w in verse.findall("tei:w", ns):
                    word_text = w.text.strip() if w.text else ""
                    if word_text:
                        words_with_source.append((source, word_text))

        return words_with_source, verse_lengths

    def save_results(self, word_freq_path="statistics/word_frequencies_by_source.csv", verse_length_path="statistics/verse_lengths_by_source.csv"):
        self.word_freq_source_df.to_csv(word_freq_path, index=False, encoding="utf-8-sig")
        self.verse_length_df.to_csv(verse_length_path, index=False, encoding="utf-8-sig")

excel_path = "books_to_sources.xlsx"

xml_files = {
"Genesis":  'SHEBANQ/Genesis.xml',
"Exodus":  'SHEBANQ/Exodus.xml',
"Leviticus": 'SHEBANQ/Leviticus.xml',
"Numbers":  'SHEBANQ/Numbers.xml',
"Deuteronomy": 'SHEBANQ/Deuteronomy.xml'
}

# Activation of the Class
analyzer = BibleTextAnalyzer(excel_path, xml_files)
analyzer.extract_data()  
analyzer.save_results()  

# =====================  phrase frequencies for each source =====================

def analyze_phrase_frequencies(input_excel, output_excel):
    """
    Reads the Excel file, calculates the frequency of 'Function' and 'Phrase Type' per source,
    and exports the results to a new Excel file with two sheets.
    """
    df = pd.read_excel(input_excel)

    # Calculating Function frequencies for each source
    function_counts = df.pivot_table(index="Source", columns="Function", aggfunc="size", fill_value=0)
    function_counts = function_counts.reset_index()

    # Calculating Phrase Type frequencies for each Source
    phrase_type_counts = df.pivot_table(index="Source", columns="Phrase Type", aggfunc="size", fill_value=0)
    phrase_type_counts = phrase_type_counts.reset_index()

    # Saving to an excel file with two sheets
    with pd.ExcelWriter(output_excel) as writer:
        function_counts.to_excel(writer, sheet_name="Function Frequencies", index=False)
        phrase_type_counts.to_excel(writer, sheet_name="Phrase Type Frequencies", index=False)


input_excel = "clause_structure_by_source.xlsx"
output_excel = "statistics/phrase_frequencies_by_source.xlsx"

analyze_phrase_frequencies(input_excel, output_excel)

# =====================  unique words for each source =====================

class UniqueWordsBySourceAnalyzer:
    def __init__(self, excel_path, xml_files):
        self.excel_path = excel_path
        self.xml_files = xml_files
        self.verse_to_source = self._load_verse_mapping()
        self.verse_length_data = []

    def _load_verse_mapping(self):
        df = pd.read_excel(self.excel_path)
        verse_mapping = {}
        for _, row in df.iterrows():
            verse_mapping[(row["Book"].lower(), int(row["Chapter"]), int(row["Verse"]))] = row["Source"]
        return verse_mapping

    def extract_unique_word_counts(self):
        # Processes all verses from all XML files and calculates the number of unique words by source
        for book, path in self.xml_files.items():
            verse_lengths = self._extract_from_xml(path, book)
            self.verse_length_data.extend(verse_lengths)

        self.verse_length_df = pd.DataFrame(
            self.verse_length_data, columns=["Source", "Total Words", "Unique Words"]
        )

    def _extract_from_xml(self, file_path, book_name):
        # Reads an XML file and extracts a number of unique words for each verse by source
        verse_lengths = []
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {"tei": "http://www.tei-c.org/ns/1.0"} 

        for verse in root.findall(".//tei:s", ns):
            verse_id = verse.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")
            parts = verse_id.split(".")
            if len(parts) >= 4:
                chapter = int(parts[-2])
                verse_num = int(parts[-1])
                book_lower = book_name.lower()

                # Searching for a source in the verse according to the Excel file
                source = self.verse_to_source.get((book_lower, chapter, verse_num), "Unknown")

                # Extracting all the words in the verse
                words = [w.text.strip() for w in verse.findall("tei:w", ns) if w.text]

                # Calculation of the number of general and unique words
                total_words = len(words)
                unique_words = len(set(words))

                verse_lengths.append((source, total_words, unique_words))

        return verse_lengths
    # Calculating the average number of unique words by source
    def compute_average_unique_words(self):
        self.average_words_df = self.verse_length_df.groupby("Source")[["Total Words", "Unique Words"]].mean().reset_index()
        
        print("\n Average unique words by source:")
        print(self.average_words_df)   

    def save_results(self, output_path="statistics/unique_words_by_source.csv"):
        self.verse_length_df.to_csv(output_path, index=False, encoding="utf-8-sig")


excel_path = "books_to_sources.xlsx"

xml_files = {
    "Genesis": 'SHEBANQ/Genesis.xml',
    "Exodus": 'SHEBANQ/Exodus.xml',
    "Leviticus": 'SHEBANQ/Leviticus.xml',
    "Numbers": 'SHEBANQ/Numbers.xml',
    "Deuteronomy": 'SHEBANQ/Deuteronomy.xml'
}

# Activate the class
analyzer = UniqueWordsBySourceAnalyzer(excel_path, xml_files)
analyzer.extract_unique_word_counts()  
analyzer.compute_average_unique_words()  
analyzer.save_results()  

# =====================  dependency tree depth per source =====================

# File paths divided by source
source_files = {
    'P': "dicta_by_source/dicta_P.json",
    'R': "dicta_by_source/dicta_R.json",
    'J': "dicta_by_source/dicta_J.json",
    'E': "dicta_by_source/dicta_E.json",
    'D1': "dicta_by_source/dicta_D1.json",
    'D2': "dicta_by_source/dicta_D2.json",
    'Dn': "dicta_by_source/dicta_Dn.json",
    'O': "dicta_by_source/dicta_O.json"
}

def compute_tree_depth(tokens):
    tree = {}
    for idx, token in enumerate(tokens):
        head_idx = token['syntax'].get('dep_head_idx', None)
        if head_idx is not None:
            if head_idx not in tree:
                tree[head_idx] = []
            tree[head_idx].append(idx)

    def depth(node):
        if node not in tree:
            return 1
        return 1 + max(depth(child) for child in tree[node])

    return depth(-1)

all_verse_depths = []

# Going through all the sources
for source, filename in source_files.items():
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        for verse in data:
            chapter = verse.get('chapter', 'Unknown')
            verse_number = verse.get('verse', 'Unknown')
            predictions = verse.get('prediction', [])

            if predictions:
                tokens = predictions[0].get('tokens', [])
                if tokens:
                    depth = compute_tree_depth(tokens)
                    all_verse_depths.append({
                        'Source': source,
                        'Chapter': chapter,
                        'Verse': verse_number,
                        'Depth': depth
                    })

depths_df = pd.DataFrame(all_verse_depths)


csv_path = "statistics/dependency_depths_by_source.csv"
depths_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

# Average dependency tree depth per source
average_depth_per_source = depths_df.groupby('Source')['Depth'].mean().reset_index()
average_depth_per_source.columns = ['Source', 'Average Depth']

print("\n Average dependency tree depth per source:")
print(average_depth_per_source)

# =====================  teamim tree depth per source =====================

def calculate_depth(lines, start_index):
    max_depth = 0
    for i in range(start_index + 1, len(lines)):
        line = lines[i].strip('\n')
        if line.startswith('source:'):
            break  
        depth = line.count('│') + line.count('└') + line.count('├')
        if depth > max_depth:
            max_depth = depth
    return max_depth

with open('teamim-trees_by_source.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# In-depth analysis according to sources
source_depths = []
current_source = None

for i, line in enumerate(lines):
    if line.startswith('source:'):
        current_source = line.split(': ')[1].strip()
        if current_source.lower() == "unknown":  
            continue
        depth = calculate_depth(lines, i)
        source_depths.append({'Source': current_source, 'Depth': depth})

source_depths_df = pd.DataFrame(source_depths)
source_depths_df.to_csv('statistics/teamim_depths_by_source.csv', index=False, encoding='utf-8-sig')

# Average teamim depth per source
average_depth_per_source = source_depths_df.groupby('Source')['Depth'].mean().reset_index()
average_depth_per_source.columns = ['Source', 'Average Depth']

print("\n Average teamim depth per source:")
print(average_depth_per_source)

# =====================  number of clauses per source - by Teamim =====================

clause_counts_by_source = defaultdict(list)

with open('teamim-clauses_by_source.txt', 'r', encoding='utf-8') as file:
    current_source = None
    clause_count = 0

    for line in file:
        line = line.strip()

        if line.startswith("source:"):
            current_source = line.split(":")[1].strip()
            clause_count = 0  

        elif line.startswith("0.") or line.startswith("1."):
            clause_count += 1

        # If there is an active source, keep the number of verses for it
        if current_source:
            clause_counts_by_source[current_source].append(clause_count)

# Filtering unknown sources
clause_counts_by_source = {src: counts for src, counts in clause_counts_by_source.items() if src.lower() != "unknown"}

# Calculation of average clause by source
average_clauses_per_source = pd.DataFrame({
    'Source': list(clause_counts_by_source.keys()),
    'Average Clauses per Source': [sum(clauses) / len(clauses) if len(clauses) > 0 else 0 for clauses in clause_counts_by_source.values()]
})

print("\n Average number of clauses per source - by Teamim:")
print(average_clauses_per_source)

# =====================  number of clauses per source - by clauses structure =====================

file_path = 'clause_structure_by_source.xlsx'
df = pd.read_excel(file_path)

# Counting unique verses for each verse
clause_counts_excel = df.groupby('Sentence ID')['Clause ID'].nunique().reset_index()
clause_counts_excel.columns = ['Sentence ID', 'Clause Count']

# Connecting the source for each verse
clause_counts_excel = pd.merge(clause_counts_excel, df[['Sentence ID', 'Source']].drop_duplicates(), on='Sentence ID')

# Filtering unknown sources
clause_counts_excel = clause_counts_excel[clause_counts_excel['Source'].str.lower() != 'unknown']

# Calculation of average clauses by source
average_clauses_per_source = clause_counts_excel.groupby('Source')['Clause Count'].mean().reset_index()
average_clauses_per_source.columns = ['Source', 'Average Clauses per Verse']


print("\n Average number of clauses per verse by source - by clauses structure:")
print(average_clauses_per_source)

# =====================  word frequencies per source =====================

file_path = "statistics/word_frequencies_by_source.csv"
word_frequencies_df = pd.read_csv(file_path)

# Count the number of times each word appears in each source
word_counts_by_source = word_frequencies_df.groupby(['Source', 'Word']).size().reset_index(name='Word_Frequency')

# Count the number of different words in each source
distinct_words_per_source = word_counts_by_source.groupby('Source').size().reset_index(name='Unique_Words')

# Count the total number of words in each source
total_words_per_source = word_frequencies_df.groupby('Source')['Count'].sum().reset_index(name='Total_Words')

# Merge the data together
unique_words_analysis = total_words_per_source.merge(distinct_words_per_source, on='Source', how='left')

# Calculate the percentage of unique words for each source
unique_words_analysis['Unique_Words_Percentage'] = (unique_words_analysis['Unique_Words'] / unique_words_analysis['Total_Words']) * 100

print("\n Number of unique words:")
print(unique_words_analysis)
