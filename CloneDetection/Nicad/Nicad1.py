import os
import json
from itertools import combinations
from multiprocessing import Pool, cpu_count
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
    
    for json_file in json_files:
        result = process_json_file(json_file)
        code_dict.update(result)
    
    return code_dict

def initialize_worker(code_dict):
    global global_code_dict
    global_code_dict = code_dict

def calculate_similarity(combination_chunk):
    results = []
    for f1, f2 in combination_chunk:
        similarity = get_similarity(global_code_dict[f1], global_code_dict[f2])
        if similarity >= 0.7:
            print(f'{f1}  {f2}  {similarity}')
        results.append((f1, f2, similarity))
    return results

def chunk_combinations(combinations_list, num_chunks):
    chunk_size = len(combinations_list) // num_chunks
    return [combinations_list[i:i + chunk_size] for i in range(0, len(combinations_list), chunk_size)]

def main(input_dir, num_workers, limit):
    code_dict = process_json_files(input_dir, limit)
    
    code_combinations = list(combinations(code_dict.keys(), 2))
    combination_chunks = chunk_combinations(code_combinations, num_workers)
    
    similarities = {}
    clones = []
    threshold = 0.70
    
    with Pool(processes=num_workers, initializer=initialize_worker, initargs=(code_dict,)) as pool:
        results = pool.map(calculate_similarity, combination_chunks)
    
    for chunk_results in results:
        for f1, f2, similarity in chunk_results:
            if similarity > threshold:
                clones.append((f1, f2))
                print(f'Clone detected between {f1} and {f2} with similarity {similarity}')
            similarities[(f1, f2)] = similarity
    
    with open('clone_report.txt', 'w') as report:
        report.write('Detected clones (similarity > 0.70):\n')
        for f1, f2 in clones:
            pid1, id1 = f1.split('_')
            pid2, id2 = f2.split('_')
            report.write(f'{pid1}:{id1}|{pid2}:{id2}\n')
            
    return similarities, clones

if __name__ == "__main__":
    input_dir = "/PathTo/DNNForest"
    num_workers = min(64, cpu_count())  # Ensure we don't exceed the CPU count
    limit = 100
    start = time.time()
    similarities, clones = main(input_dir, num_workers, limit)
    end = time.time()
    extime = int(end - start)
    print(f"Execution time: {extime} seconds")
