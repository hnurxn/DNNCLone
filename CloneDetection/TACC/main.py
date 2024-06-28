import os
import json
import hashlib
import mmh3
from collections import defaultdict
from tokenize4py import line_tokenize, just_splittoken
from LVMapper import locate_clones
from SourcererCC import SourcererCC_Similarity, generate_GPT, getCodeBlock, sortBlockWithGPT, sort_gloPT
from AST import generate_ast_and_features, compare_features

__GloPT__ = dict()

def extract_code_from_json(json_data):
    code_dict = {}
    line_dict = {}
    project_id = json_data["Project_id"]
    for item in json_data["Forest"]:
        unique_id = f"{project_id}_{item['Id']}"
        code_dict[unique_id] = item["Code"]
        line_dict[unique_id] = line_tokenize(item["Code"])
    return code_dict, line_dict

def get_murmurhash(lines):
    combined_lines = '\n'.join(lines)
    return mmh3.hash128(combined_lines)

def build_inverted_index(code_dict, n):
    inverted_index = {}
    hash_dict = {}
    for func_id, code_lines in code_dict.items():
        if len(code_lines) < n:
            continue  # Skip code segments with less than n lines
        hash_dict[func_id] = []
        for i in range(len(code_lines) - n + 1):
            n_lines = code_lines[i:i + n]
            hash_value = get_murmurhash(n_lines)
            hash_dict[func_id].append(hash_value)
            if hash_value not in inverted_index:
                inverted_index[hash_value] = set()
            inverted_index[hash_value].add(func_id)
    return inverted_index, hash_dict

def process_json_file(json_file):
    code_dict = {}
    ast_dict = {}
    line_dict = {}
    with open(json_file, 'r') as f:
        json_input = json.load(f)
        code_temp, line_temp = extract_code_from_json(json_input)
        code_dict.update(code_temp)
        line_dict.update(line_temp)
        for item in json_input["Forest"]:
            unique_id = f"{json_input['Project_id']}_{item['Id']}"
            combined_code = item["Code"]
            try:
                ast_dict[unique_id] = generate_ast_and_features(combined_code)
            except Exception as e:
                print(f"Error processing {unique_id}: {e}")
    return code_dict, line_dict, ast_dict

def process_json_files(input_dir, limit=500):
    code_dict = {}
    line_dict = {}
    ast_dict = {}
    json_files = sorted([os.path.join(root, file) for root, _, files in os.walk(input_dir) for file in files if file.endswith(".json")])[400:500]
    
    for json_file in json_files:
        file_code_dict, file_line_dict, file_ast_dict = process_json_file(json_file)
        code_dict.update(file_code_dict)
        line_dict.update(file_line_dict)
        ast_dict.update(file_ast_dict)
    
    return code_dict, line_dict, ast_dict

def main(input_dir, n, max_files):
    # Preprocessing: Generate inverted index and hash dictionary
    code_dict, line_dict, ast_dict = process_json_files(input_dir, max_files)
    inverted_index, hash_dict = build_inverted_index(line_dict, n)
    # print(len(code_dict), len(inverted_index), len(hash_dict))

    # Generate global token frequency statistics
    all_blocks = []
    for c in code_dict.values():  # Combine code line lists into a single string
        all_blocks.append(c)
    generate_GPT(all_blocks, __GloPT__)  # Pass __GloPT__ as a parameter to the function
    sort_gloPT(__GloPT__)  # Also pass __GloPT__ as a parameter to the function
    
    # Localization: Use inverted index and hash dictionary to locate possible clone pairs
    clone_pairs, Sim_list, second_level_candidates = locate_clones(inverted_index, hash_dict)
    # print(len(clone_pairs), len(second_level_candidates))
    # SourcererCC similarity determination
    third_level_candidates = []
    for f1, f2 in second_level_candidates:
        code1 = code_dict[f1]
        code2 = code_dict[f2]
        
        similarity = SourcererCC_Similarity(code1, code2, __GloPT__)
        # print("SourcererCC",similarity)
        if similarity >= 0.7:  # Final similarity threshold
            clone_pairs.append((f1, f2))
            print("SourcererCC",similarity)
            Sim_list.append(similarity)
        elif 0.4 <= similarity < 0.7:  # Third level similarity threshold
            third_level_candidates.append((f1, f2))
    print("num of third",len(third_level_candidates))
    # Deduplication of third-level clone candidates
    for f1, f2 in third_level_candidates:
        ast1 = ast_dict[f1]
        ast2 = ast_dict[f2]
        similarity = compare_features(ast1, ast2)
        print("AST",similarity)
        if similarity >= 0.65:
            clone_pairs.append((f1, f2))
            Sim_list.append(similarity)
    # Store all clones
    with open('clone_report.txt', 'w') as report:
        # report.write('Detected clones (similarity > 0.70):\n')
        for i in range(len(clone_pairs)):
            pid1, id1 = clone_pairs[i][0].split('_')
            pid2, id2 = clone_pairs[i][1].split('_')
            report.write(f'{pid1}:{id1}|{pid2}:{id2}\n')


if __name__ == "__main__":
    input_dir = "/bdata2/AISystemEvaluation/DNNForest"
    n = 3  # Assume we want to process 3-line blocks; adjust as needed
    max_files = 100  # Limit the total number of JSON files to read to 500
    main(input_dir, n, max_files)
