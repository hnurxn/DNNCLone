import os  
import pdb
import ast
import logging
import json
import chardet
import re
import datetime
import pandas as pd
from dependency import set_dependencies_of_nn_modules, set_dependencies_of_nn_modules_with_import_deps

from utils import is_containing_same_name

ID_count = 0 # Global value


class RemoveConstantSharp(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = node.value.replace('#','')
        return node
     
class RemovePrints(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
            return None
        return node

def _count_line_of_code(class_code_list):
    line = 0
    for ClassCode in class_code_list:
        line += len(ClassCode['Code'].split('\n')) - ClassCode['Code'].split('\n').count('')
    return line

def _get_dir_size_bydu(dir, depth=0):
    res_list = os.popen(f'du {dir} -h --max-depth={depth}')

    res_list = [x.split('\t') for x in res_list]

    return res_list[0][0]

def parse_and_remove_irrelevant_code(code):
    tree = ast.parse(code)
    RemoveConstantSharp().visit(tree) # 去除掉字符串#号 返回tree
    return tree

def source_code_translate(source_code):
    match_Module = re.search(r"from torch.nn import Module as \w+\n" , source_code)     #Module
    if match_Module:
        return match_Module.group(0)[31:-1]
    else: 
        return None

def remove_comment(source_code):
    cleaned_code = re.sub(r'(\'\'\'(.*?)\'\'\'|\"\"\"(.*?)\"\"\")', '', source_code, flags=re.MULTILINE | re.DOTALL)
    return cleaned_code

def extract_python_class(source_code, file_path):
    global ID_count

    class_definitions = []
    # extract useless code comments and find out the way define model 
    def_str = source_code_translate(source_code)
    # Parse the source code using ast.parse and remove 'print' like useless code 
    parsed_code = parse_and_remove_irrelevant_code(source_code)
    # Traverse the AST and find the class node  
    for node in ast.walk(parsed_code):  
        if isinstance(node, ast.ClassDef): 
            class_code = ast.unparse(node)
            class_regex = r"class\s+\w+\s*\((.*?)\):" 
            match = re.search(class_regex, class_code) 
            if match and (match.group(1).find('nn.Module') == 0 or match.group(1).find('torch.nn.Module') == 0 or (def_str is not None and match.group(1).find(def_str) == 0)):
                class_definitions.append(
                    {
                        'Name': node.name ,
                        'Id': ID_count ,
                        'Code': remove_comment(class_code) ,
                        'Child_node': list() ,
                        'File_path': file_path
                    }
                )  
                ID_count += 1
  
    return class_definitions

def find_inherited_nn_modules(root_folder):  
    global ID_count

    inherited_modules = []  
    ID_count = 0
    for folder, sub_folders, files in os.walk(root_folder): 
        for file in files:  
            if file.endswith('.py') and not os.path.islink(folder + '/' + file):  
                with open(folder + '/' + file, 'rb') as f:   
                    encoding = chardet.detect(f.read())['encoding']
                with open(folder + '/' + file, mode = 'r', encoding =  'utf-8' if(encoding == None or encoding.startswith('Windows-')) else encoding) as f:
                    try:
                        source_code = f.read()
                        inherited_modules.extend(extract_python_class(source_code, folder + '/' + file))
                    except Exception as e:
                        logging.error('failed in parsing ' + folder + '/' + file)
                        logging.exception(e)
                        
    return inherited_modules  

def my_cmp_func(s):
    print(s.split(':')[0])
    return int(s.split(':')[0])

  
if __name__ == '__main__':  

    logging.basicConfig(filename="DNNModel_forest_extract.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.ERROR)

    root_folder = '../../../../repos'  
    storage_folder = '../../data/ASE24/jsons_final'
    Model_Forest = {}
    #ListofRepo = os.listdir(root_folder)
    #ListofRepo.sort(key = my_cmp_func)
    processed_count = 0
    non_empty_forests = 0

    df = pd.read_csv('../../data/ASE24/info_final/NameandTime.csv')
    shuffled_df = df.sample(frac=1).reset_index(drop=True)
    for index, row in shuffled_df.iterrows():
    # Extract the 'Modified' and 'pathModified' columns for the current row
        modified = row['Modified']
        path_modified = row['pathModified']
        json_path = storage_folder + '/' + modified + '.json'
        if os.path.exists(json_path):
            print('Already processed:', modified)
            continue
        Repo = path_modified
        print(Repo)
        DNNClassModuleList = find_inherited_nn_modules(root_folder + '/' + Repo)

        DNNClassModuleForest = set_dependencies_of_nn_modules_with_import_deps(DNNClassModuleList, root_folder, Repo)
        Forest = {
            'Project_id': modified.split(':')[0]    ,           # project id
            'Node_num': len(DNNClassModuleList)    ,               # forest size(or Node number)
            'LOC': _count_line_of_code(DNNClassModuleList)  ,      # Count the number of lines of code
            'Repository_size': _get_dir_size_bydu(root_folder + '/' + Repo, 0)  ,   # Repository_Size
            'Forest': DNNClassModuleForest                           #  ForestList
        }

        with open(storage_folder + '/' + modified + '.json', 'w') as f:         # each forest json will be named same with Repo
            json.dump(Forest, f)
        processed_count += 1
        if Forest['Forest']:
            non_empty_forests += 1
        
        if processed_count % 100 == 0:
            with open('../../data/ASE24/extract_progress_final_log.txt', 'a') as log_file:
                log_file.write(f"{datetime.datetime.now()}: Processed {processed_count} repositories, {non_empty_forests} non-empty forests.\n")
