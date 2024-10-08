# from collections import defaultdict
from tokenize4py import just_splittoken

def generate_GPT(code_blocks, GloPT):
    for block in code_blocks:
        for token in block:
            if token in GloPT:
                GloPT[token] += 1
            else:
                GloPT[token] = 1

def sortBlockWithGPT(block, GloPT):
    block.sort(key=lambda item: GloPT.get(item, 0))

def sort_gloPT(GloPT):
    sorted_gloPT = dict(sorted(GloPT.items(), key=lambda item: item[1]))
    GloPT.clear()
    GloPT.update(sorted_gloPT)

def getCodeBlock(code):
    return just_splittoken(code)

def overlapSimilarity(ls_1, ls_2, GloPT):
    res = 0
    len1, len2 = len(ls_1), len(ls_2)
    i_1, i_2 = 0, 0
    while i_1 < len1 and i_2 < len2:
        if ls_1[i_1] == ls_2[i_2]:
            res += 1
            i_1 += 1
            i_2 += 1
        else:
            if GloPT.get(ls_1[i_1], 0) < GloPT.get(ls_2[i_2], 0):
                i_1 += 1
            elif GloPT.get(ls_1[i_1], 0) > GloPT.get(ls_2[i_2], 0):
                i_2 += 1
            else:
                if ls_1[i_1] < ls_2[i_2]:
                    i_1 += 1
                else:
                    i_2 += 1
    return res

def get_similarity(code1, code2, GloPT):
    block1 = getCodeBlock(code1)
    block2 = getCodeBlock(code2)
    generate_GPT([block1, block2], GloPT)
    sortBlockWithGPT(block1, GloPT)
    sortBlockWithGPT(block2, GloPT)
    lcs_len = overlapSimilarity(block1, block2, GloPT)
    # print(block1)
    # print(block2)
    
    return lcs_len / max(len(block1), len(block2))

def SourcererCC_Similarity(code1, code2, GloPT):
    return get_similarity(code1, code2, GloPT)
