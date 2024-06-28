import json
import re
import os

def remove_comments_prints_and_logging(code):
    """Remove all comments, print statements, and logging statements from the code."""
    # Remove comments
    code = re.sub(r'#.*', '', code)  # Remove inline comments
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)  # Remove multi-line comments
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)  # Remove multi-line comments

    # Remove print statements
    print_pattern = r'print\s*\(.*?\)\s*'
    code = re.sub(print_pattern, '', code, flags=re.DOTALL)

    # Remove logging statements
    logging_pattern = r'logging\.(debug|info|warning|error|critical)\s*\(.*?\)\s*'
    code = re.sub(logging_pattern, '', code, flags=re.DOTALL)

    return code

def modify_code(code):
    code = remove_comments_prints_and_logging(code)
    return code

def process_forest(json_file_path, output_file_path, log_file_path):
    # Load the JSON data from the input file
    with open(json_file_path, 'r') as infile:
        data = json.load(infile)

    # Open the log file for writing
    with open(log_file_path, 'a') as log_file:
        # Iterate over each neural network node in the 'Forest' list
        for node in data.get('Forest', []):
            original_code = node.get('Code', '')
            modified_code = modify_code(original_code)
            
            node['Code'] = modified_code

    # Save the modified data to the output file
    with open(output_file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def cloneDetector(forestDir):
    forestPathList = os.listdir(forestDir)
    
    for forestPath in forestPathList:
        input_forestPath = os.path.join(forestDir, forestPath)
        output_forestPath = os.path.join("output/path", forestPath)
        log_file_path = "code_changes.txt"
        process_forest(input_forestPath, output_forestPath, log_file_path)

cloneDetector("input/path")
