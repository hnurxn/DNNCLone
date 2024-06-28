import os
import json
import pickle
from itertools import combinations
from multiprocessing import Pool
from tokenize4py import tokenize_code
import time

# Global variable to hold the code_dict in each worker process
global_code_dict = None

def extract_code_from_json(json_data):
    code_dict = {}
    project_id = json_data["Project_id"]
    for item in json_data["Forest"]:
        unique_id = f"{project_id}_{item['Id']}"
        code = item["Code"]
        lines = code.split('\n')
        if len(lines) > 100:
            continue
        code_dict[unique_id] = item["Code"]
    return code_dict

def get_similarity(block1, block2):
    m, n = len(block1), len(block2)
    if m == 0 or n == 0 or abs(m - n)/max(m, n) > 0.3:
        return 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if block1[i - 1] == block2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n] / max(m, n)

def process_json_file(json_file):
    with open(json_file, 'r') as f:
        json_input = json.load(f)
        return extract_code_from_json(json_input)

def process_json_files(input_dir, limit=1000):
    code_dict = {}
    json_files = sorted([os.path.join(root, file) for root, _, files in os.walk(input_dir) for file in files if file.endswith(".json")])[400:500]
    
    # Limit the number of JSON files to process
    # json_files = json_files[:limit]
    
    for json_file in json_files:
        result = process_json_file(json_file)
        code_dict.update(result)
    
    return code_dict

def initialize_worker(code_dict_path):
    global global_code_dict
    with open(code_dict_path, 'rb') as f:
        global_code_dict = pickle.load(f)

def calculate_similarity(args):
    f1, f2 = args
    global global_code_dict
    similarity = get_similarity(global_code_dict[f1], global_code_dict[f2])
    if similarity >= 0.7:
        print(f'{f1}  {f2}  {similarity}')
    return (f1, f2, similarity)

def main(input_dir, num_workers, limit):
    code_dict = process_json_files(input_dir, limit)
    print("1")
    # Save the code_dict to a file
    code_dict_path = 'code_dict.pkl'
    with open(code_dict_path, 'wb') as f:
        pickle.dump(code_dict, f)
    print("2")
    code_combinations = list(combinations(code_dict.keys(), 2))
    print(len(code_combinations))
    print(code_combinations[-1])
    print("3")
    similarities = {}
    clones = []
    threshold = 0.70
    
    with Pool(processes=num_workers, initializer=initialize_worker, initargs=(code_dict_path,)) as pool:
        results = pool.map(calculate_similarity, [(f1, f2) for f1, f2 in code_combinations])
    
    for f1, f2, similarity in results:
        if similarity > threshold:
            clones.append((f1, f2))
            print(f'Clone detected between {f1} and {f2} with similarity {similarity}')
        similarities[(f1, f2)] = similarity
    
    with open('clone_report1111.txt', 'w') as report:
        report.write('Detected clones (similarity > 0.70):\n')
        for f1, f2 in clones:
            pid1, id1 = f1.split('_')
            pid2, id2 = f2.split('_')
            report.write(f'{pid1}:{id1} and {pid2}:{id2}   Similarity: {round(similarities[(f1, f2)],3)}\n')
            
    return similarities, clones

if __name__ == "__main__":
    input_dir = "/bdata2/AISystemEvaluation/DNNForest"
    num_workers = 8  # Change this value to the desired number of worker processes
    limit = 100  # Set the limit to the desired number of repositories
    start = time.time()
    similarities, clones = main(input_dir, num_workers, limit)
    end = time.time()
    extime = int(end - start)
    print(f"Execution time: {extime} seconds")
