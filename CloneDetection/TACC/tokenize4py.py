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


def line_tokenize(code):
    code_lines = code.split('\n')
    tokens = []
    keywords = {'break', 'with', 'is', 'import', 'elif', 'except', 'raise', 'try', 'from',
            'class', 'as', 'del', 'assert', 'finally', 'while', 'continue', 'lambda', 'and', 'if',
            'else', 'for', 'def', 'not', 'global', 'return', 'or', 'nonlocal', 'yield', 'pass', 'in'}
    binaryOperator = {'+', '-', '*', '/', '**', '//', '%'}
    comparisonOperator = {'==', '!=', '<', '>', '<=', '>='}
    for line in code_lines:
        line_token = ""
        if line.strip() == '':
            continue
        for tok in tokenize.tokenize(io.BytesIO(line.encode('utf-8')).readline):
            tok_type = tokenize.tok_name[tok.type]
            if tok_type in ['NL', 'NEWLINE', 'INDENT', 'DEDENT','ENDMARKER', 'ENCODING',"COMMENT"]:
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
            line_token += token
        tokens.append(line_token)
        lines= list(filter(lambda x: x.strip(), tokens))
    return lines


def just_splittoken(code):
    tokens = []
    for tok in tokenize.tokenize(io.BytesIO(code.encode('utf-8')).readline):
        tok_type = tokenize.tok_name[tok.type]
        if tok_type in ['NL', 'NEWLINE', 'INDENT', 'DEDENT','ENDMARKER', 'ENCODING', "OP","COMMENT"]:
            continue
        tokens.append(tok.string)
    return tokens


# code_snippets = ["""def test1(a,b):\n #  asdsad\nc = a + b\nreturn 1""","""def test2(c,d):\ne = c + d\nreturn 2"""
# ]

# for code in code_snippets:

#     print(line_tokenize(code))
