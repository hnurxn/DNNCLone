import os
import json
import re
from itertools import combinations
from clone_detector import CloneDetector
import time

# Model ID and device settings
model_id = "../LLMs/codegm/base"
gpu_device = "cuda:0"  # Specify the GPU device

# Initialize the CloneDetector
clone_detector = CloneDetector(model_id=model_id, device=gpu_device)

def extract_code_from_json(json_data):
    code_dict = {}
    project_id = json_data["Project_id"]
    for item in json_data["Forest"]:
        unique_id = f"{project_id}_{item['Id']}"
        code_dict[unique_id] = item["Code"]
    return code_dict

def process_json_files(input_dir, limit=2):
    code_dict = {}
    repo_count = 0

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json"):
                json_file = os.path.join(root, file)
                with open(json_file, 'r') as f:
                    json_input = json.load(f)
                    code_dict.update(extract_code_from_json(json_input))
                
                repo_count += 1
                if repo_count >= limit:
                    break  # Properly exit the loop when limit is reached

    return code_dict

def yes_no_to_binary(text):
    # Find a match of 'YES' or 'NO' (case-insensitive)
    match = re.search(r'\b(YES|NO)\b', text, flags=re.IGNORECASE)
    # Convert match to binary
    if match:
        return 1 if match.group(0).lower() == 'yes' else 0
    else:
        return 0

def main(input_dir):
    code_dict = process_json_files(input_dir, limit=2)
    
    code_combinations = combinations(code_dict.keys(), 2)
    match_time = 0
    results = []
    start = time.time()
    for f1, f2 in code_combinations:
        match_time += 1
        res = clone_detector.get_response(code_dict[f1], code_dict[f2])
        binary_value = yes_no_to_binary(res)
        results.append((f1, f2, binary_value))
        print(f1, f2, binary_value)
    end = time.time()
    # Save the results to a text file
    output_file = 'clone_results.txt'
    with open(output_file, 'w') as f:
        for f1, f2, binary_value in results:
            if binary_value:
                f.write(f"{f1}, {f2}: {binary_value}\n")
    
    print(f"Results saved to {output_file}")
    excute_time = int(end - start)
    print(f"Match Times: {match_time}, excution time: {excute_time}")
if __name__ == "__main__":
    input_dir = "/mnt/nfs/ssd2bdata/data/ASE24/json_start"
    main(input_dir)
    