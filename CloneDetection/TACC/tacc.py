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
            continue  # 跳过行数少于n的代码段
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
    # 预处理阶段：生成倒排索引和哈希字典
    code_dict, line_dict, ast_dict = process_json_files(input_dir, max_files)
    inverted_index, hash_dict = build_inverted_index(line_dict, n)
    # print(len(code_dict), len(inverted_index), len(hash_dict))

    # 生成全局token频率统计
    all_blocks = []
    for c in code_dict.values():  # 将代码行列表连接成一个字符串
        all_blocks.append(c)
    generate_GPT(all_blocks, __GloPT__)  # 将__GloPT__作为参数传递给函数
    sort_gloPT(__GloPT__)  # 也需要将__GloPT__作为参数传递给函数
    
    # 定位阶段：使用倒排索引和哈希字典定位可能的克隆对
    clone_pairs, Sim_list, second_level_candidates = locate_clones(inverted_index, hash_dict)
    # print(len(clone_pairs), len(second_level_candidates))
    # SourcererCC相似度判定
    third_level_candidates = []
    for f1, f2 in second_level_candidates:
        code1 = code_dict[f1]
        code2 = code_dict[f2]
        
        similarity = SourcererCC_Similarity(code1, code2, __GloPT__)
        # print("SourcererCC",similarity)
        if similarity >= 0.7:  # 最终相似度阈值
            clone_pairs.append((f1, f2))
            print("SourcererCC",similarity)
            Sim_list.append(similarity)
        elif 0.4 <= similarity < 0.7:  # 第三级别相似度阈值
            third_level_candidates.append((f1, f2))
    print("num of third",len(third_level_candidates))
    # 第三级别克隆候选对去重
    for f1, f2 in third_level_candidates:
        ast1 = ast_dict[f1]
        ast2 = ast_dict[f2]
        similarity = compare_features(ast1, ast2)
        print("AST",similarity)
        if similarity >= 0.65:
            clone_pairs.append((f1, f2))
            Sim_list.append(similarity)
    # 将所有克隆进行存储
    with open('clone_report.txt', 'w') as report:
        # report.write('Detected clones (similarity > 0.70):\n')
        for i in range(len(clone_pairs)):
            pid1, id1 = clone_pairs[i][0].split('_')
            pid2, id2 = clone_pairs[i][1].split('_')
            report.write(f'{pid1}:{id1}|{pid2}:{id2}\n')


if __name__ == "__main__":
    input_dir = "/bdata2/AISystemEvaluation/DNNForest"
    n = 3  # 假设我们想要处理3行的块，可以根据需要调整
    max_files = 100  # 限制读取的JSON文件总数为500
    main(input_dir, n, max_files)