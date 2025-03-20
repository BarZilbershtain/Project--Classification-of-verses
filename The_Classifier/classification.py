import json
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report
import pandas as pd

# ---- step 1: reading the files ----
files = {
    "Genesis": "dicta/Genesis_dicta.json",
    "Exodus": "dicta/Exodus_dicta.json",
    "Leviticus": "dicta/Leviticus_dicta.json",
    "Numbers": "dicta/numbers_dicta.json",
    "Deuteronomy": "dicta/Deuteronomy_dicta.json"
}

# Mapping book names to numbers according to trees.py
book_map = {
    "Genesis": "0",
    "Exodus": "1",
    "Leviticus": "2",
    "Numbers": "3",
    "Deuteronomy": "4"
}

# Function for extracting roots (lemmas) and parts of speech (POS)
def extract_features(entry):
    words = []
    lemmas = []
    pos_tags = []
    
    for token in entry["prediction"][0]["tokens"]:
        words.append(token["token"])  
        lemmas.append(token["lex"])  
        pos_tags.append(token["morph"]["pos"]) 

    return " ".join(words), " ".join(lemmas), " ".join(pos_tags)

# Loading the verses and their book + releasing additional features
verses = []
lemmas_list = []
pos_list = []
labels = []
verse_ids = []

for label, file_path in files.items():
    book_number = book_map[label]
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            verse_id = f"{book_number}:{entry['chapter']}:{entry['verse']}"
            words, lemmas, pos_tags = extract_features(entry)  # שליפת מאפיינים

            verses.append(words)
            lemmas_list.append(lemmas)
            pos_list.append(pos_tags)
            labels.append(label)
            verse_ids.append(verse_id)

# ---- step 2: reading the dependency tree (teamim-trees.txt) ----
tree_file_path = "teamim-trees.txt"

trees = {}
with open(tree_file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    current_verse = None
    tree_structure = []

    for line in lines:
        line = line.strip()
        if line.startswith("P:"):
            if current_verse is not None and tree_structure:
                trees[current_verse] = " ".join(tree_structure)
            current_verse = line.split("P:")[-1].strip()
            tree_structure = []
        elif line:
            tree_structure.append(line)

    if current_verse is not None and tree_structure:
        trees[current_verse] = " ".join(tree_structure)

# ---- step 3: Integrate all features separately ----
combined_texts_words = []
combined_texts_lemmas = []
combined_texts_pos = []
combined_texts_tree = []

num_with_tree = 0  

for verse_id, words, lemmas, pos_tags in zip(verse_ids, verses, lemmas_list, pos_list):
    tree_info = trees.get(verse_id, "")  
    if tree_info:
        num_with_tree += 1  
    combined_texts_words.append(words)
    combined_texts_lemmas.append(lemmas)
    combined_texts_pos.append(pos_tags)
    combined_texts_tree.append(tree_info)

# ---- step 4: processing with TF-IDF separately for each feature ----
vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=5000)

# separate features
X_words = vectorizer.fit_transform(combined_texts_words)
X_lemmas = vectorizer.fit_transform(combined_texts_lemmas)
X_pos = vectorizer.fit_transform(combined_texts_pos)
X_tree = vectorizer.fit_transform(combined_texts_tree)

y_combined = np.array(labels)

# ---- step 5: training and evaluating the model separately for each feature ----
clf_rf = RandomForestClassifier(n_estimators=100, random_state=42)
clf_svm = SVC(kernel="linear", C=1.0, random_state=42)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

def evaluate_model(X, y):
    cv_scores_rf = cross_val_score(clf_rf, X, y, cv=cv, scoring='accuracy')
    cv_scores_svm = cross_val_score(clf_svm, X, y, cv=cv, scoring='accuracy')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    clf_rf.fit(X_train, y_train)
    clf_svm.fit(X_train, y_train)

    y_pred_rf = clf_rf.predict(X_test)
    y_pred_svm = clf_svm.predict(X_test)

    cv_accuracy_rf = np.mean(cv_scores_rf)
    cv_accuracy_svm = np.mean(cv_scores_svm)
    classification_results_rf = classification_report(y_test, y_pred_rf, output_dict=True)
    classification_results_svm = classification_report(y_test, y_pred_svm, output_dict=True)

    return cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm

# Calculate results for each feature separately
all_results = {}

# words feature
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_words, y_combined)
all_results["Words"] = (classification_results_rf, classification_results_svm)

# lemmas feature
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_lemmas, y_combined)
all_results["Lemmas"] = (classification_results_rf, classification_results_svm)

# POS feature
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_pos, y_combined)
all_results["POS"] = (classification_results_rf, classification_results_svm)

# tree feature 
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_tree, y_combined)
all_results["Tree"] = (classification_results_rf, classification_results_svm)

# ---- step 6: processing with TF-IDF for all features together ----
combined_texts_all = [words + " " + lemmas + " " + pos_tags + " " + tree_info
                    for words, lemmas, pos_tags, tree_info in zip(combined_texts_words, combined_texts_lemmas, combined_texts_pos, combined_texts_tree)]

# TF-IDF processing for all features together
X_all = vectorizer.fit_transform(combined_texts_all)

# Calculate results for all features together
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_all, y_combined)
all_results["All Features"] = (classification_results_rf, classification_results_svm)

# ---- step 7: processing with TF-IDF for the features words and lemmas together ----
combined_texts_words_lemmas = [words + " " + lemmas
                            for words, lemmas in zip(combined_texts_words, combined_texts_lemmas)]

# TF-IDF processing for the features words and lemmas together
X_words_lemmas = vectorizer.fit_transform(combined_texts_words_lemmas)

# Calculate results for the features words and lemmas together
cv_accuracy_rf, cv_accuracy_svm, classification_results_rf, classification_results_svm = evaluate_model(X_words_lemmas, y_combined)
all_results["Words + Lemmas"] = (classification_results_rf, classification_results_svm)

# ---- step 8: saving the results to an Excel file ----
with pd.ExcelWriter('classification_results.xlsx') as writer:
    for feature_name, (classification_results_rf, classification_results_svm) in all_results.items():
        # יצירת DataFrame עבור כל מאפיין
        df_rf = pd.DataFrame(classification_results_rf).transpose()
        df_svm = pd.DataFrame(classification_results_svm).transpose()

        # כתיבה לגיליון מתאים
        df_rf.to_excel(writer, sheet_name=f"RF_{feature_name}")
        df_svm.to_excel(writer, sheet_name=f"SVM_{feature_name}")


print("התוצאות נשמרו בהצלחה בקובץ 'classification_results.xlsx'")
