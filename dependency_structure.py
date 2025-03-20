from transformers import AutoTokenizer, AutoModel
from xml.etree import ElementTree as ET
import torch
import json

# Load the XML file
xml_file = "TANACH.US/Deuteronomy.xml"  

"""We ran the same code separately for each of the books by changing the XML file, because it has a long runtime."""

tree = ET.parse(xml_file)
root = tree.getroot()

# Find all <v> tags that represent verses
verse_outputs = []
for c in root.findall(".//c"):  # Iterating through <c> elements (chapter)
    for v in c.findall(".//v"):  # Iterating through <v> elements (verses)
        verse_number = v.attrib.get("n")  # Get the verse number from attribute 'n'
        
        # Collect words in the current verse
        words = [word.text for word in v.findall(".//w")]  # Get all words in <w> tags
        
        # Join words into a single string for the verse
        verse_text = " ".join(words)

        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained('dicta-il/dictabert-tiny-joint')
        model = AutoModel.from_pretrained('dicta-il/dictabert-tiny-joint', trust_remote_code=True)

        # Set model to evaluation mode
        model.eval()

        # Perform prediction for the current verse
        output = model.predict([verse_text], tokenizer, output_style='json')

        verse_output = {
            "chapter": c.attrib.get("n"),  
            "verse": verse_number,
            "text": verse_text,
            "prediction": output
        }

        verse_outputs.append(verse_output)

        # Save the output to a JSON file after each verse
        with open("dicta/Deuteronomy_dicta.json", "w", encoding="utf-8") as json_file:
            json.dump(verse_outputs, json_file, indent=2, ensure_ascii=False)

