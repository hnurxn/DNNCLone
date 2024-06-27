import os
import subprocess
import shlex

import pdb

def run_command(cmd):
    FNULL = open(os.devnull, 'w')
    sub_p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
    return sub_p.communicate()[0].decode('utf-8', 'strict')

def build_deps_dict(deps_list):
    deps_dict = dict()
    for name in deps_list:
        if name.endswith(':'):
            deps_dict[name[0:-1]] = list()
            current_file = name[0:-1]
        elif name != '':
            deps_dict[current_file].append(name)
    return deps_dict

def get_import_deps(cmd):
    deps_list = run_command(cmd).replace(' ', '').split('\n')
    deps = build_deps_dict(deps_list)
    
    return deps

def is_unique_name(DNNClassNameIDList, name):
    return sum(1 for item in DNNClassNameIDList if item["Name"] == name) == 1

def get_possible_callee_class(DNN_class_list, name):
    possible_callee = []
    for DNN_class in DNN_class_list:
        if DNN_class['Name'] == name:
            possible_callee.append(DNN_class)
    return possible_callee

def is_containing_same_name_file(deps):          # Judge whether we should deal with '.'
    for key, value in deps.items():    
        if key.find('.') >= 0:
            return True
    return False
    
def file_path_translate(file_path, deps):
    if is_containing_same_name_file(deps):
        file_path = file_path.replace('.py', '').split('/', maxsplit = 5)[-1].replace('/', '.')
    else:
        file_path = file_path.replace('.py', '').split('/')[-1]
    return file_path

def pruning(name):
    return name.startswith('torch') or name.startswith('numpy')

def bfs_locate_outer_callee(deps, caller_file_path, possible_callee_list):
    bfs_rotate_list = [caller_file_path]        
    cnt = 0

    while bfs_rotate_list != []:
        cnt += 1
        if cnt > 10000:
            break
        file_path = bfs_rotate_list[0]
        bfs_rotate_list.pop(0)
        if pruning(file_path):
            continue
        else:
            for possible_callee in possible_callee_list:
                callee_file_path = file_path_translate(possible_callee['File_path'], deps)
                if file_path == callee_file_path:
                    return possible_callee['Id']
                else:
                    if file_path in deps:
                        bfs_rotate_list.extend(deps[file_path])
    return -1

def locate_callee_index(deps, DNN_class_list, DNNClassNameIDList, callee_NameAndIdDict, caller_file_path):
    if is_unique_name(DNNClassNameIDList, callee_NameAndIdDict['Name']):
        return callee_NameAndIdDict['Id']
    else:
        possible_callee_list = get_possible_callee_class(DNN_class_list, callee_NameAndIdDict['Name'])
        caller_file_path = file_path_translate(caller_file_path, deps)

        index = bfs_locate_outer_callee(deps, caller_file_path, possible_callee_list)
        return index

# for extract.py

def is_containing_same_name(module_list):
    DNNClassNameSet = set()
    DNNClassNameList = list()
    for DNNCodeClass_iter in module_list:
        DNNClassNameSet.add(DNNCodeClass_iter['Name'])
        DNNClassNameList.append(DNNCodeClass_iter['Name'])  
    return (len(DNNClassNameList) != len(DNNClassNameSet)) 


