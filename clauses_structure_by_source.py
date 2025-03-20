import pandas as pd

def merge_bible_data(file1_path, file2_path, sheet_name1="Sheet1", sheet_name2="Sheet1"):
    # Load the Excel files
    xls1 = pd.ExcelFile(file1_path)
    xls2 = pd.ExcelFile(file2_path)
    
    # Read data from the specified sheets
    df1 = pd.read_excel(xls1, sheet_name=sheet_name1)
    df2 = pd.read_excel(xls2, sheet_name=sheet_name2)
    
    # Standardize column names for merging
    df1["Book"] = df1["Book"].str.lower()
    df2["Book"] = df2["Book"].str.lower()
    
    # Merge the datasets based on 'Book', 'Chapter', and 'Verse'
    merged_df = pd.merge(df1, df2, on=["Book", "Chapter", "Verse"], how="inner")
    
    return merged_df

# Example usage
file1_path = "clauses_structure.xlsx"
file2_path = "books_to_sources.xlsx"
merged_df = merge_bible_data(file1_path, file2_path)

# Save the merged data to a new Excel file
merged_df.to_excel("clause_structure_by_source.xlsx", index=False)

# Display the first few rows of the merged data
#print(merged_df.head())
