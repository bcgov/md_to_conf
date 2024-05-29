import os
import base64
import requests
import pandas as pd
import subprocess
import argparse

def get_auth_header(username, token):
    return {
        'Authorization': 'Basic ' + base64.b64encode(f"{username}:{token}".encode()).decode('utf-8'),
        'Content-Type': 'application/json'
    }

def get_page_id(base_url, headers, space_key, title):
    search_url = f"{base_url}/rest/api/content?title={title}&spaceKey={space_key}&expand=history.lastUpdated"
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200 and response.json()['size'] > 0:
        return response.json()['results'][0]['id']
    return None

def ensure_pages_exist(base_url, path_parts, username, token, space_key):
    headers = get_auth_header(username, token)
    ancestor_title = None

    for part in path_parts:
        page_title = part.replace('_', ' ').replace('.md', '')  # Correctly format page title
        if not page_title:
            continue
        page_id = get_page_id(base_url, headers, space_key, page_title)
        
        if page_id:
            ancestor_title = page_title
        else:
            data = {
                "type": "page",
                "title": page_title,
                "ancestors": [{"id": get_page_id(base_url, headers, space_key, ancestor_title)}] if ancestor_title else [],
                "space": {"key": space_key},
                "body": {
                    "storage": {
                        "value": "<p>Created automatically by the script.</p>",
                        "representation": "storage"
                    }
                }
            }
            create_url = f"{base_url}/rest/api/content"
            create_response = requests.post(create_url, headers=headers, json=data)
            if create_response.status_code != 200:
                print(f"Failed to create page {page_title}, error: {create_response.text}")
                return None
            ancestor_title = page_title
            print(f"Created page {page_title} with ID {create_response.json()['id']}")

    return ancestor_title  # Return the title of the last created or found page

def parse_parent_page_and_path(link):
    parts = [part.strip() for part in link.split('\\') if part.strip()]
    print(f"Parsed parts: {parts}")  # Debug statement
    if len(parts) > 1:
        parent_page_parts = parts[:-1]
        full_path = '\\\\' + '\\'.join(parts)
        if not full_path.lower().endswith('.md'):
            full_path += '.md'
        print(f"Parent parts: {parent_page_parts}, Full path: {full_path}")  # Debug statement
        return parent_page_parts, full_path
    return [], ""

def migrate_documents(username, token, base_url, space_key):
    df = pd.read_excel('updated_report.xlsx')

    # Add a new column for migration status if not already present
    if 'Migrated' not in df.columns:
        df['Migrated'] = False

    for index, row in df.iterrows():
        if row['File Type'] == 'md' and not df.at[index, 'Migrated']:
            path_parts, full_md_path = parse_parent_page_and_path(row['Link'])
            print(f"Full MD Path: {full_md_path}")  # Debug statement
            if os.path.exists(full_md_path):
                try:
                    # Read and process the markdown file
                    with open(full_md_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Remove the specific text block if it exists
                    text_block = """
<!-- ########################ALREADY MIGRATED################### ############################ -->
<!-- # THIS FILE WAS MIGRATED TO CONFLUENCE ON YYYY-MM-DD # -->
<!-- # PLEASE DO NOT UPDATE THIS FILE, UPDATE THE CORRESPONDING FILE ON CONFLUENCE INSTEAD # -->
<!-- ############################################ ######################################## -->
"""
                    if content.startswith(text_block):
                        content = content[len(text_block):]

                    # Write the cleaned content back to the file
                    with open(full_md_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    last_page_title = ensure_pages_exist(base_url, path_parts, username, token, space_key)
                    if last_page_title:
                        command = f'python md2conf.py "{full_md_path}" {space_key} -a "{last_page_title}" -u "{username}" -p "{token}" -o dpdd'
                        print(f"Running command: {command}")  # Debug statement
                        result = subprocess.run(command, shell=True, capture_output=True)
                        print(f"Command output: {result.stdout.decode()}")  # Debug statement
                        print(f"Command error: {result.stderr.decode()}")  # Debug statement
                        if result.returncode == 0:
                            df.at[index, 'Migrated'] = True
                        else:
                            df.at[index, 'Migrated'] = False
                    else:
                        print(f"Failed to ensure Confluence page structure for {full_md_path}")
                        df.at[index, 'Migrated'] = False
                except Exception as e:
                    print(f"Error processing file {full_md_path}: {e}")
                    df.at[index, 'Migrated'] = False
            else:
                print(f"Error: Markdown file does not exist: {full_md_path}")
                df.at[index, 'Migrated'] = False

    # Save the updated Excel file
    df.to_excel('updated_report.xlsx', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate markdown documents to Confluence pages.")
    parser.add_argument("-u", "--username", default=os.environ.get('CONFLUENCE_USERNAME'), help="Confluence username.")
    parser.add_argument("-p", "--apikey", default=os.environ.get('CONFLUENCE_API_KEY'), help="Confluence API key.")
    parser.add_argument("-b", "--baseurl", default=os.environ.get('CONFLUENCE_BASE_URL'), help="Confluence base URL.")
    parser.add_argument("-s", "--spacekey", default=os.environ.get('CONFLUENCE_SPACE_KEY'), help="Confluence space key.")
    args = parser.parse_args()

    migrate_documents(args.username, args.apikey, args.baseurl, args.spacekey)










