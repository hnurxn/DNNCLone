import json
import re
import os

def replace_class_and_base_names(code):
    """Replace class name and base class name with 'ClassName' and 'Module'."""
    class_pattern = r"class\s+(\w+)\s*\(.*?\):"
    base_pattern = r"class\s+\w+\s*\((.*?)\):"
    
    class_match = re.search(class_pattern, code)
    base_match = re.search(base_pattern, code)
    
    if class_match and base_match:
        original_class_name = class_match.group(1)
        original_base_name = base_match.group(1)
        
        code = re.sub(rf"\b{re.escape(original_class_name)}\b", "ClassName", code)
        code = re.sub(rf"\b{re.escape(original_base_name)}\b", "Module", code)
        
    return code

def replace_parameters(code):
    """Replace parameters in __init__ and forward functions with 'parameter1', 'parameter2', etc."""
    param_counter = 1
    
    def replace_func_parameters(match):
        nonlocal param_counter
        params = [p.strip() for p in match.group(2).split(',') if p.strip() != 'self']
        
        new_params = ['self'] + [f"param{param_counter + i}" for i in range(len(params))]
        param_map = dict(zip(params, new_params[1:]))

        # Replace parameter names in the function body
        func_body = match.group(3)
        for old_param, new_param in param_map.items():
            func_body = re.sub(rf"\b{re.escape(old_param.split('=')[0].strip())}\b", new_param, func_body)

        param_counter += len(params)
        # Return the new function definition
        func_name = match.group(1).split('(')[0].strip()
        return f"{func_name}({', '.join(new_params)}):\n\t{func_body}"

    init_pattern = r"(def __init__\s*\((.*?)\))\s*:\s*(.*?)(?=\n\s*def |$)"
    forward_pattern = r"(def forward\s*\((.*?)\))\s*:\s*(.*?)(?=\n\s*def |$)"
    
    code = re.sub(init_pattern, replace_func_parameters, code, flags=re.DOTALL)
    code = re.sub(forward_pattern, replace_func_parameters, code, flags=re.DOTALL)
    
    return code

def replace_variables(code):
    """Replace variables in __init__ method with 'variable1', 'variable2', etc."""
    vars_map = {}
    def replace_func_variables(match):
        func_body = match.group(2)
        var_lines = [line for line in func_body.split('\n') if '=' in line and 'self.' in line]
        new_vars = [f"variable{i+1}" for i in range(len(var_lines))]

        for var_line, new_var in zip(var_lines, new_vars):
            parts = var_line.split('=')
            left_part = parts[0].strip()
            if 'self.' in left_part:
                try:
                    original_var = left_part.split('self.')[1]
                    vars_map[original_var] = new_var
                    func_body = re.sub(rf"\b{re.escape(original_var)}\b", new_var, func_body)
                except IndexError:
                    continue

        return f"{match.group(1)}:\n\t{func_body}\n"

    init_pattern = r"(def __init__\s*\(.*?\))\s*:\s*(.*?)(?=\ndef |$)"
    code = re.sub(init_pattern, replace_func_variables, code, flags=re.DOTALL)
    
    for old_var, new_var in vars_map.items():
        code = re.sub(rf"\b{re.escape(old_var)}\b", new_var, code)
    
    return code

def replace_forward_variables(code):
    """Replace variables in forward method with 'variable1', 'variable2', etc."""
    def replace_func_variables(match):
        func_body = match.group(2)
        var_lines = func_body.split('\n')
        new_vars = {}
        var_counter = 1

        for i in range(len(var_lines)):
            line = var_lines[i]
            if '=' in line and re.match(r"^\s*[\w\.]+\s*=\s*[^=]", line):
                parts = line.split('=')
                left_part = parts[0].strip()
                if left_part not in new_vars:
                    new_var = f"temp{var_counter}"
                    new_vars[left_part] = new_var
                    var_counter += 1
                else:
                    new_var = new_vars[left_part]
                var_lines[i] = re.sub(rf"\b{re.escape(left_part)}\b", new_var, line)
                for j in range(i + 1, len(var_lines)):
                    var_lines[j] = re.sub(rf"\b{re.escape(left_part)}\b", new_var, var_lines[j])

        return match.group(1) + ":\n\t" + '\n'.join(var_lines) + "\n"

    forward_pattern = r"(def forward\s*\(.*?\))\s*:\s*(.*?)(?=\ndef |$)"
    code = re.sub(forward_pattern, replace_func_variables, code, flags=re.DOTALL)

    return code

def modify_code(code):
    code = replace_class_and_base_names(code)
    code = replace_parameters(code)
    code = replace_variables(code)
    code = replace_forward_variables(code)
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
    codeIDList = []
    zeroForestNum = 0
    
    for forestPath in forestPathList:
        input_forestPath = os.path.join(forestDir, forestPath)
        output_forestPath = os.path.join("output/path", forestPath)
        log_file_path = "code_changes.txt"
        process_forest(input_forestPath, output_forestPath, log_file_path)

cloneDetector("input/path")
