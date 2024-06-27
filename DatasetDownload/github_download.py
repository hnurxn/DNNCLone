import os
import shutil
import subprocess
import pandas as pd
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# Function to sanitize folder names
def sanitize_folder_name(name):
    return name.replace('/', ':')

# Function to check the size of the repository
def get_repo_size(clone_url, token):
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}'
        }
        repo_api_url = clone_url.replace('.git', '').replace('https://github.com/', 'https://api.github.com/repos/')
        response = requests.get(repo_api_url, headers=headers)
        
        if response.status_code == 200:
            repo_info = response.json()
            size_kb = repo_info.get('size', 0)
            return size_kb / 1024  # Convert KB to MB
        elif response.status_code == 403 and 'rate limit' in response.text.lower():
            log_constraints(clone_url, response.status_code, response.text)
            return float('inf')
        else:
            print(f"Error fetching repo size: {response.status_code} {response.text}")
            return float('inf')
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return float('inf')

# Function to get the default branch of the repository
def get_default_branch(clone_url, token):
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}'
        }
        repo_api_url = clone_url.replace('.git', '').replace('https://github.com/', 'https://api.github.com/repos/')
        response = requests.get(repo_api_url, headers=headers)
        
        if response.status_code == 200:
            repo_info = response.json()
            return repo_info.get('default_branch', 'main')
        elif response.status_code == 403 and 'rate limit' in response.text.lower(): 
            log_constraints(clone_url, response.status_code, response.text)
            return 'main'
        else:
            print(f"Error fetching default branch: {response.status_code} {response.text}")
            return 'main'
    # Catches any RequestException that may occur during the request (e.g., network issues, invalid URL).
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return 'main'

# Function to log constraints
def log_constraints(clone_url, status_code, message):
    with open('constraints.log', 'a') as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{clone_url},{status_code},{message}\n")

# Function to clone only .py and .pth files using sparse checkout
def sparse_clone(order, name, clone_url, base_dir, token, pth_log):
    folder_name = f"{order}:{sanitize_folder_name(name)}"
    repo_path = os.path.join(base_dir, folder_name)

    os.makedirs(repo_path)

    # Initialize a new git repository
    subprocess.run(['git', 'init'], cwd=repo_path, check=True)
    
    # Set sparse checkout to true
    subprocess.run(['git', 'config', 'core.sparseCheckout', 'true'], cwd=repo_path, check=True)
    
    # Define sparse checkout patterns
    with open(os.path.join(repo_path, '.git', 'info', 'sparse-checkout'), 'w') as f:
        f.write('*.py\n')
        f.write('*.pth\n')
    
    # Add the remote origin
    subprocess.run(['git', 'remote', 'add', 'origin', clone_url], cwd=repo_path, check=True)
    
    # Get the default branch
    default_branch = get_default_branch(clone_url, token)
    
    # Pull the repository
    try:
        subprocess.run(['git', 'pull', 'origin', default_branch], cwd=repo_path, check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to pull {clone_url}")
        return []

    # Check for .pth files and log the repository name if found
    pth_files = []
    pth_found = False
    for root, _, files in os.walk(repo_path, topdown=False):
        for file in files:
            if file.endswith('.pth'):
                pth_files.append(order)
                # Log the repository name and order
                with open(pth_log, 'a') as log_file:
                    log_file.write(f"{order},{name}\n")
                # Remove the .pth file
                os.remove(os.path.join(root, file))
                pth_found = True

    # Remove .git directory to save space
    shutil.rmtree(os.path.join(repo_path, '.git'))

    if pth_found:
        return [order]
    else:
        return []

def process_repository(row, token, base_dir, pth_log):
    order = row['order']
    name = row['name']
    clone_url = row['clone_url']
    folder_name = f"{order}:{sanitize_folder_name(name)}"
    repo_path = os.path.join(base_dir, folder_name)

    # Check if the directory already exists
    if os.path.exists(repo_path):
        print(f"Skipping {clone_url} because {repo_path} already exists.")
        return

    repo_size = get_repo_size(clone_url, token)
    print(f"Repo size for {clone_url}: {repo_size} MB")  # Log the repo size
    if repo_size < 100:
        sparse_clone(order, name, clone_url, base_dir, token, pth_log)
    else:
        print(f"Skipping {clone_url} due to size constraints")

def main():
    csv_file = 'YOURPATH/github_get.csv'
    base_dir = 'YOURPATH/repositories'
    pth_log = 'YOURPATH/contain_pth.csv'
    constraints_log = 'constraints.log'
    tokens = [
        'YOURTOKEN1',
        'YOURTOKEN2',
    ]

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Ensure the pth_log file exists
    if not os.path.exists(pth_log):
        with open(pth_log, 'w') as log_file:
            log_file.write("Order,Repository Name\n")

    # Ensure the constraints_log file exists
    if not os.path.exists(constraints_log):
        with open(constraints_log, 'w') as log_file:
            log_file.write("Time,Repository URL,Status Code,Message\n")

    df = pd.read_csv(csv_file)

    with ThreadPoolExecutor(max_workers=len(tokens)) as executor:
        futures = []
        for i, row in df.iterrows():
            token = tokens[i % len(tokens)]  # Rotate tokens
            futures.append(executor.submit(process_repository, row, token, base_dir, pth_log))

        for future in futures:
            future.result()  # Wait for all futures to complete

if __name__ == "__main__":
    main()
