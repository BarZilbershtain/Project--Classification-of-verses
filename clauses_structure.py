import xml.etree.ElementTree as ET
import os
import pandas as pd


def parse_syntactic_structure_with_words(file_path):
    """
    Parse XML and extract syntactic structures while adding chapter and verse numbers.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    results = []
    book_name = os.path.basename(file_path).replace(".xml", "")

    # Find all chapters
    for chapter in root.findall(".//tei:div2", namespaces):
        chapter_number = chapter.attrib.get("DisplayName_Eng", "").replace("Chapter ", "")

        # Find all verses within the chapter
        for pasuk in chapter.findall(".//tei:s", namespaces):
            pasuk_number = pasuk.attrib.get("DisplayName_Eng", "").replace("Pasuk ", "")

            # Find all syntactic structures within the verse
            syntactic_info = pasuk.find(".//tei:syntacticInfo", namespaces)
            if syntactic_info is not None:
                for sentence in syntactic_info.findall(".//tei:sentence", namespaces):
                    sentence_id = sentence.attrib.get("id", "Unknown")

                    clauses = sentence.findall(".//tei:clause", namespaces)
                    for clause in clauses:
                        clause_id = clause.attrib.get("id", "Unknown")
                        phrases = clause.findall(".//tei:phrase", namespaces)
                        for phrase in phrases:
                            phrase_id = phrase.attrib.get("id", "Unknown")
                            function = phrase.attrib.get("function", "Unknown")
                            phrase_type = phrase.attrib.get("type", "Unknown")

                            results.append({
                                "Book": book_name, 
                                "Chapter": chapter_number,
                                "Verse": pasuk_number,
                                "Sentence ID": sentence_id,
                                "Clause ID": clause_id,
                                "Phrase ID": phrase_id,
                                "Function": function,
                                "Phrase Type": phrase_type,
                            })
    return results


def process_files_to_excel(file_paths, output_file):
    """
    Process multiple XML files and export results to Excel.
    """
    all_results = []
    for file_path in file_paths:
        print(f"Processing: {file_path}")
        results = parse_syntactic_structure_with_words(file_path)
        all_results.extend(results)

    df = pd.DataFrame(all_results)
    
    column_order = ["Book", "Chapter", "Verse", "Sentence ID", "Clause ID", "Phrase ID", "Function", "Phrase Type"]
    df = df[column_order]
    
    df.to_excel(output_file, index=False)
    print(f"Results exported to {output_file}")

files = [
    'SHEBANQ/Genesis.xml',
    'SHEBANQ/Exodus.xml',
    'SHEBANQ/Leviticus.xml',
    'SHEBANQ/Numbers.xml',
    'SHEBANQ/Deuteronomy.xml'
]

# Process files and export results to Excel
output_excel = "clauses_structure.xlsx"
process_files_to_excel(files, output_excel)
