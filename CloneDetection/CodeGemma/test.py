import os
import json
import re
import time
import torch.multiprocessing as mp
from itertools import combinations
from clone_detector import CloneDetector

# Model ID
model_id = "../LLMs/codegm/base"

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

def process_json_files(input_dir, limit=100):
    code_dict = {}
    json_files = sorted([os.path.join(root, file) for root, _, files in os.walk(input_dir) for file in files if file.endswith(".json")])[400:500]

    for json_file in json_files:
        with open(json_file, 'r') as f:
            json_input = json.load(f)
            code_dict.update(extract_code_from_json(json_input))

    return code_dict

def yes_no_to_binary(text):
    match = re.search(r'\b(YES|NO)\b', text, flags=re.IGNORECASE)
    return 1 if match and match.group(0).lower() == 'yes' else 0

def worker(code_dict, code_combinations, gpu_device, output_file):
    clone_detector = CloneDetector(model_id=model_id, device=gpu_device)
    results = []

    for f1, f2 in code_combinations:
        res = clone_detector.get_response(code_dict[f1], code_dict[f2])
        binary_value = yes_no_to_binary(res)
        results.append((f1, f2, binary_value))
        print(f"{f1}, {f2}, {binary_value}")

    with open(output_file, 'w') as f:
        for f1, f2, binary_value in results:
            if binary_value:
                f.write(f"{f1}, {f2}: {binary_value}\n")

    print(f"Results saved to {output_file} on {gpu_device}")

def main(input_dir):
    num_gpus = 2
    output_files = [f'clone_results_gpu{i}.txt' for i in range(num_gpus)]
    process_list = []

    code_dict = process_json_files(input_dir, limit=100)  # Limit to first 100 files
    code_keys = list(code_dict.keys())
    code_combinations = list(combinations(code_keys, 2))
    print(len(code_combinations))
    print(code_combinations[-1])
    # split_index = len(code_combinations) * 4 // 6  # Split index for 4/6 and 2/6
    # code_combinations_part = code_combinations[split_index:]
    # chunk_size = len(code_combinations_part) // num_gpus

    # start_time = time.time()

    # for i in range(num_gpus):
    #     start_idx = i * chunk_size
    #     end_idx = len(code_combinations_part) if i == num_gpus - 1 else (i + 1) * chunk_size
    #     p = mp.Process(target=worker, args=(code_dict, code_combinations_part[start_idx:end_idx], f'cuda:{i}', output_files[i]))
    #     process_list.append(p)
    #     p.start()
    
    # for p in process_list:
    #     p.join()

    # end_time = time.time()

    # print(f"Total execution time: {int(end_time - start_time)} seconds")

if __name__ == "__main__":
    input_dir = "PathTo/json_start"
    main(input_dir)
