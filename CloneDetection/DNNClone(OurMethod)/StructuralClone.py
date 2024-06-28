import ast
import torch.nn as nn

def parse_network_layers(class_code):
    """Parse network layers and their order from a given class code."""
    tree = ast.parse(class_code)
    
    layers = []
    forward_order = []
    layer_dict = {}
    
    class NetworkVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            if any(isinstance(base, ast.Attribute) and base.attr == 'Module' for base in node.bases):
                for body_item in node.body:
                    if isinstance(body_item, ast.FunctionDef):
                        if body_item.name == '__init__':
                            self.visit_Init(body_item)
                        elif body_item.name == 'forward':
                            self.visit_Forward(body_item)
        
        def visit_Init(self, node):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(stmt.value, ast.Call):
                            layer_name = target.attr
                            if hasattr(stmt.value.func, 'attr'):
                                layer_type = stmt.value.func.attr
                                layers.append((layer_name, layer_type))
                                layer_dict[layer_name] = layer_type

        def visit_Forward(self, node):
            for stmt in node.body:
                self.visit(stmt)
        
        def visit_Call(self, node):
            func = node.func
            if isinstance(func, ast.Attribute):
                layer_name = func.attr
                if layer_name in layer_dict:
                    forward_order.append(layer_dict[layer_name])
            for arg in node.args:
                if isinstance(arg, ast.Call):
                    self.visit_Call(arg)
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Call):
                    self.visit_Call(keyword.value)

    visitor = NetworkVisitor()
    visitor.visit(tree)
    
    return layers, forward_order

# Example input
class_code = '''
Code Example
'''

# Call the function and print results
layers, forward_order = parse_network_layers(class_code)

print("List of all network layers:")
for layer in layers:
    print(layer)

print("\nOrder of layers in forward pass:")
for layer in forward_order:
    print(layer)

# New function to analyze and store the forward logic
def analyze_forward_logic(class_code):
    """Analyze and store the forward logic based on __init__ defined layers."""
    tree = ast.parse(class_code)
    forward_logic = []
    layer_dict = {}

    class ForwardAnalyzer(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            if any(isinstance(base, ast.Attribute) and base.attr == 'Module' for base in node.bases):
                for body_item in node.body:
                    if isinstance(body_item, ast.FunctionDef):
                        if body_item.name == '__init__':
                            self.visit_Init(body_item)
                        elif body_item.name == 'forward':
                            self.visit_Forward(body_item)

        def visit_Init(self, node):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(stmt.value, ast.Call):
                            layer_name = target.attr
                            if hasattr(stmt.value.func, 'attr'):
                                layer_type = stmt.value.func.attr
                                layer_dict[layer_name] = layer_type

        def visit_Forward(self, node):
            for stmt in node.body:
                self.visit(stmt)
        
        def visit_Call(self, node):
            func = node.func
            if isinstance(func, ast.Attribute):
                layer_name = func.attr
                if layer_name in layer_dict:
                    forward_logic.append(layer_name)
            for arg in node.args:
                if isinstance(arg, ast.Call):
                    self.visit_Call(arg)
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Call):
                    self.visit_Call(keyword.value)
        
        def visit_Assign(self, node):
            if isinstance(node.value, ast.Call):
                self.visit_Call(node.value)
            self.generic_visit(node)
        
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call):
                self.visit_Call(node.value)
            self.generic_visit(node)

    analyzer = ForwardAnalyzer()
    analyzer.visit(tree)
    
    return forward_logic

# Call the new function and print results
forward_logic = analyze_forward_logic(class_code)

print("\nForward logic order:")
for layer in forward_logic:
    print(layer)
