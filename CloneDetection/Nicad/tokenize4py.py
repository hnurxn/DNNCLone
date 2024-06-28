import tokenize
import io

def tokenize_code(code, isNormalize=False):
    tokens = []
    keywords = {'break', 'with', 'is', 'import', 'elif', 'except', 'raise', 'try', 'from',
            'class', 'as', 'del', 'assert', 'finally', 'while', 'continue', 'lambda', 'and', 'if',
            'else', 'for', 'def', 'not', 'global', 'return', 'or', 'nonlocal', 'yield', 'pass', 'in'}
    binaryOperator = {'+', '-', '*', '/', '**', '//', '%'}
    comparisonOperator = {'==', '!=', '<', '>', '<=', '>='}
    for tok in tokenize.tokenize(io.BytesIO(code.encode('utf-8')).readline):
        tok_type = tokenize.tok_name[tok.type]
        if tok_type in ['NL', 'NEWLINE', 'INDENT', 'DEDENT','ENDMARKER', 'ENCODING']:
            continue
        if tok.string in keywords:
            token = tok.string
        elif tok.string in binaryOperator:
            token = '+'
        elif tok.string in comparisonOperator:
            token = '=='
        elif tok_type == 'NUMBER':
            token = '0'
        elif tok_type == 'STRING':
            token = "s"
        elif tok_type == 'NAME':
            token = 'x'
        else:
            token = tok.string
    
        tokens.append(token)
    
    return tokens
        