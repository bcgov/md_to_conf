
import os
import pandas as pd

# Load the data
file_path = 'updated_report.xlsx'
data = pd.read_excel(file_path)

# Filter to only markdown files
markdown_files = data[data['File Type'] == 'md']

# Text block to prepend
text_block = """
<!-- ########################ALREADY MIGRATED################### ############################ -->
<!-- # THIS FILE WAS MIGRATED TO CONFLUENCE ON YYYY-MM-DD # -->
<!-- # PLEASE DO NOT UPDATE THIS FILE, UPDATE THE CORRESPONDING FILE ON CONFLUENCE INSTEAD # -->
<!-- ############################################ ######################################## -->
"""

# Function to prepend text to each markdown file
def prepend_text_to_files(files_df, text):
    update_log = []
    for index, row in files_df.iterrows():
        file_path = row['Link']
        try:
            # Read the current contents of the file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Prepend the text block
            updated_content = text + content
            
            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            
            update_log.append(f'Successfully updated: {file_path}')
        except Exception as e:
            update_log.append(f'Failed to update {file_path}: {e}')
    
    return update_log

# Execute the function and print the log results
log_results = prepend_text_to_files(markdown_files, text_block)
for log in log_results:
    print(log)
