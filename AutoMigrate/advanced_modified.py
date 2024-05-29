
import re

def remove_html_comments(content):
    # Regular expression to match the HTML comments added to the Markdown files
    comment_pattern = re.compile(r'<!-- #######################ALREADY MIGRATED#####.*?##################################### -->', re.DOTALL)
    # Remove the comments from the content
    return comment_pattern.sub('', content)
import pandas as pd
import subprocess
import os
import sys
import requests
import base64

def get_auth_header(username, token):
    """
    Creates the authorization header for API requests.
    """
    return {
        'Authorization': 'Basic ' + base64.b64encode(f"{username}:{token}".encode()).decode('utf-8'),
        'Content-Type': 'application/json'
    }

# def ensure_pages_exist(base_url, path_parts, username, token, space_key):
#     """
#     Ensures that all pages specified in the path exist in Confluence, creating them as needed.
#     Returns the ID of the last page in the path (deepest child).
#     """
#     headers = get_auth_header(username, token)
#     ancestor_id = None  # Start with no ancestor ID, or set this to the ID of the root page in your space if necessary

#     for part in path_parts:
#         page_title = part.replace('_', ' ')
#         # Check if the page exists
#         search_url = f"{base_url}/rest/api/content?title={page_title}&spaceKey={space_key}&expand=history.lastUpdated"
#         response = requests.get(search_url, headers=headers)
#         if response.status_code == 200 and response.json()['size'] > 0:
#             ancestor_id = response.json()['results'][0]['id']
#         else:
#             # Create the page if it does not exist
#             data = {
#                 "type": "page",
#                 "title": page_title,
#                 "ancestors": [{"id": ancestor_id}] if ancestor_id else [],
#                 "space": {"key": space_key},
#                 "body": {
#                     "storage": {
#                         "value": "<p>Created automatically by the script.</p>",
#                         "representation": "storage"
#                     }
#                 }
#             }
#             create_url = f"{base_url}/rest/api/content"
#             create_response = requests.post(create_url, headers=headers, json=data)
#             if create_response.status_code == 200:
#                 ancestor_id = create_response.json()['id']
#             else:
#                 print(f"Failed to create page {page_title}, error: {create_response.text}")
#                 return None

#     return ancestor_id

def ensure_pages_exist(base_url, path_parts, username, token, space_key):
    """
    Ensures that all pages specified in the path exist in Confluence, creating them as needed.
    Returns the name of the last page in the path (deepest child).
    """
    headers = get_auth_header(username, token)
    last_page_name = None  # Initialize the last page name

    for part in path_parts:
        page_title = part.replace('_', ' ')
        last_page_name = page_title  # Update the last page name on each loop iteration
        search_url = f"{base_url}/rest/api/content?title={page_title}&spaceKey={space_key}&expand=history.lastUpdated"
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200 and response.json()['size'] > 0:
            ancestor_id = response.json()['results'][0]['id']
        else:
            data = {
                "type": "page",
                "title": page_title,
                "ancestors": [{"id": ancestor_id}] if ancestor_id else [],
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

    return last_page_name

def parse_parent_page_and_path(link):
    """
    Extracts the parent page path and the full markdown file path from a given link.
    Adjusts network paths to ensure correct formatting for file operations.
    """
    parts = [part.strip() for part in link.split('\\') if part.strip()]
    if len(parts) > 2:
        parent_page_parts = parts[:-1]  # Exclude the markdown filename part
        full_path = '\\\\' + '\\'.join(parts)
        if not full_path.lower().endswith('.md'):
            full_path += '.md'  # Only append .md if it's not already there
        return parent_page_parts, full_path
    return [], ""


def migrate_documents(contains_sensitive_words, username, token, base_url, space_key):
    """
    Migrates documents based on the user's preference for handling sensitive words.
    """
    df = pd.read_excel('updated_report.xlsx')
    if contains_sensitive_words.lower() == 'no':
        df_filtered = df[df['Contains Sensitive Words'].str.lower() == 'no']
    else:
        df_filtered = df
    
    for index, row in df_filtered.iterrows():
        if row['File Type'] == 'md':
            path_parts, full_md_path = parse_parent_page_and_path(row['Link'])
            if os.path.exists(full_md_path):  # Check if the markdown file actually exists
                last_page_name = ensure_pages_exist(base_url, path_parts, username, token, space_key)  # Capture the returned page name here
                if last_page_name:
                    command = f"python md2conf.py \"{full_md_path}\" {space_key} -a \"{last_page_name}\" -u \"{username}\" -p \"{token}\" -o dpdd"
                    subprocess.run(command, shell=True)
                else:
                    print(f"Failed to ensure Confluence page structure for {full_md_path}")
            else:
                print(f"Error: Markdown file does not exist: {full_md_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python advanced.py <yes/no>")
        sys.exit(1)

    username = 'kejia.wang@gov.bc.ca'
    token = '4E3UJmVHVzZinzaMJ2CM6A6E'
    base_url = 'https://dpdd.atlassian.net/wiki'
    space_key = '~63b85c94082abdd71bb77ba3'
    
    migrate_documents(sys.argv[1], username, token, base_url, space_key)



























# import pandas as pd
# import subprocess
# import os
# import sys
# import requests

# def create_or_get_page(title, ancestor_id, space_key, base_url, auth):
#     """
#     Creates a Confluence page or retrieves its ID if it already exists.
#     """
#     # Check if page exists
#     search_url = f"{base_url}/rest/api/content?title={title}&spaceKey={space_key}&expand=history"
#     response = requests.get(search_url, headers={"Authorization": auth})
#     results = response.json().get('results', [])
#     if results:
#         return results[0]['id']
    
#     # Create page if not exists
#     url = f"{base_url}/rest/api/content"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": auth
#     }
#     data = {
#         "type": "page",
#         "title": title,
#         "ancestors": [{"id": ancestor_id}],
#         "space": {"key": space_key},
#         "body": {
#             "storage": {
#                 "value": f"<p>Auto-generated page for {title}</p>",
#                 "representation": "storage"
#             }
#         }
#     }
#     response = requests.post(url, headers=headers, json=data)
#     if response.status_code in [200, 201]:
#         return response.json()['id']
#     else:
#         print("Failed to create page:", response.json())
#         return None

# def migrate_documents(contains_sensitive_words, base_url, space_key, username, api_key):
#     """
#     Migrates documents based on the user's preference for handling sensitive words.
#     """
#     df = pd.read_excel('updated_report.xlsx')
#     if contains_sensitive_words.lower() == 'no':
#         df_filtered = df[df['Contains Sensitive Words'].str.lower() == 'no']
#     else:
#         df_filtered = df
    
#     auth = f"Basic {api_key}"
#     root_page_id = 'ROOT_PAGE_ID'  # You need to specify this according to your Confluence setup
    
#     for index, row in df_filtered.iterrows():
#         if row['File Type'] == 'md':
#             parts = row['Link'].split('\\')
#             current_ancestor_id = root_page_id
#             for part in parts[:-1]:  # Exclude the markdown file name
#                 page_id = create_or_get_page(part, current_ancestor_id, space_key, base_url, auth)
#                 if page_id:
#                     current_ancestor_id = page_id
#             full_md_path = '\\\\' + '\\'.join(parts)
#             if os.path.exists(full_md_path):
#                 command = f"python md2conf.py \"{full_md_path}\" ~63b85c94082abdd71bb77ba3 -a \"{parts[-2]}\" -u {username} -p {api_key} -o {space_key}"
#                 subprocess.run(command, shell=True)
#             else:
#                 print(f"Error: Markdown file does not exist: {full_md_path}")

# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python advanced.py <yes/no>")
#         sys.exit(1)
    
#     base_url = 'https://your-confluence-url.com'
#     space_key = 'YOUR_SPACE_KEY'
#     username = 'your_username'
#     api_key = 'your_api_key'
#     migrate_documents(sys.argv[1], base_url, space_key, username, api_key)




# Assuming `markdown_content` holds the markdown data loaded from a file
markdown_content = remove_html_comments(markdown_content)
