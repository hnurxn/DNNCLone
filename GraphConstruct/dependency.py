import json
import re
import ast
import pdb
import logging

import os

from utils import get_import_deps, locate_callee_index

logging.basicConfig(filename="DNNModel_forest_transform.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.ERROR)

class CodeVisitor(ast.NodeVisitor):
    def __init__(self, target_Name):
        self.target_Name = target_Name
        self.called = False
 
    def visit_Name(self, node):
        if node.id == self.target_Name:
            self.called = True

    def visit_Attribute(self, node):
        if node.attr == self.target_Name and node.value.id not in ['nn', 'torch']:
            self.called = True

def set_dependencies_of_nn_modules(DNN_class_list):
    DNNClassNameIDList = [{'Name':DNNClass['Name'], 'Id':DNNClass['Id']} for DNNClass in DNN_class_list]
    for DNNCodeClass in DNN_class_list:
        for NameAndIdDict in DNNClassNameIDList:
            if NameAndIdDict['Name'] != DNNCodeClass['Name']:
                try:
                    parsed_code = ast.parse(DNNCodeClass['Code'])
                    tree_visitor = CodeVisitor(NameAndIdDict['Name'])
                    tree_visitor.visit(parsed_code)
                    if tree_visitor.called:
                        DNN_class_list[int(DNNCodeClass['Id'])]['Child_node'].append(NameAndIdDict['Id'])
                except Exception as e:
                    logging.error('failed in analyzing code in ' + DNNCodeClass['Name'])
                    logging.exception(e)
    return DNN_class_list

def set_dependencies_of_nn_modules_with_import_deps(DNN_class_list, root_folder, Repo):
    DNNClassNameIDList = [{'Name':DNNClass['Name'], 'Id':DNNClass['Id']} for DNNClass in DNN_class_list]
    deps = get_import_deps('findimports ' + root_folder + '/' + Repo + ' --ignore-stdlib')
    for DNNCodeClass in DNN_class_list:
        for NameAndIdDict in DNNClassNameIDList:
            if NameAndIdDict['Name'] != DNNCodeClass['Name']:
                try:
                    parsed_code = ast.parse(DNNCodeClass['Code'])
                    tree_visitor = CodeVisitor(NameAndIdDict['Name'])
                    tree_visitor.visit(parsed_code)
                    if tree_visitor.called:
                        index = locate_callee_index(deps, DNN_class_list, DNNClassNameIDList, NameAndIdDict, DNNCodeClass['File_path'])
                        if index != -1 and index not in DNN_class_list[int(DNNCodeClass['Id'])]['Child_node']:
                            DNN_class_list[int(DNNCodeClass['Id'])]['Child_node'].append(index)
                except Exception as e:
                    logging.error('failed in analyzing code in ' + DNNCodeClass['Name'])
                    logging.exception(e)
    return DNN_class_list
