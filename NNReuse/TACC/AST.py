import ast
from anytree import AnyNode
from collections import defaultdict


def get_token(node):
    return type(node).__name__

def get_child(node):
    return [child for child in ast.iter_child_nodes(node)]

def createtree(root, node, nodelist, parent=None):
    token, children = get_token(node), get_child(node)
    newnode = AnyNode(id=len(nodelist), token=token, data=node, parent=parent if parent else root)
    nodelist.append(token)
    for child in children:
        createtree(root, child, nodelist, parent=newnode)

def generate_ast_and_features(source_code):
    tree = ast.parse(source_code)
    nodelist = []
    newtree = AnyNode(id=0, token=None, data=None)
    createtree(newtree, tree, nodelist)

    childrendict = {}
    fsstype(newtree, childrendict)
    id2hash, id2number = {}, {}
    HashListArray, hash_dict = get_hash(childrendict, nodelist, id2hash, id2number)
    return HashListArray, id2hash, childrendict, hash_dict

def fsstype(node, childrendict):
    children = [child.id for child in node.children]
    childrendict[node.id] = children
    for child in node.children:
        fsstype(child, childrendict)

def get_hash(childrendict, nodelist, id2hash, id2number):
    hash_dict = defaultdict(int)
    for i in reversed(range(len(childrendict))):
        token = nodelist[i]
        if not childrendict[i]:
            id2hash[i] = hash(token)
            id2number[i] = 1
        else:
            h = hash(token)
            n = 1
            for child_id in childrendict[i]:
                h += id2hash[child_id]
                n += id2number[child_id]
            id2hash[i] = h
            id2number[i] = n
        hash_dict[id2hash[i]] += 1
    HashListArray = [[] for _ in range(len(nodelist) + 1)]
    for i in range(len(id2number)):
        HashListArray[id2number[i]].append(i)
    return HashListArray, hash_dict



def mov(delnode, childrendict, id):
    for i in childrendict[id]:
        delnode.add(i)
        mov(delnode, childrendict, i)

def compare_features(features1, features2):
    delnode1, delnode2, datanode = set(), set(), []
    HashListArray1, id2hash1, childrendict1, hash_dict1 = features1
    HashListArray2, id2hash2, childrendict2, hash_dict2 = features2
    intersection = 0
    x = min(len(HashListArray1), len(HashListArray2)) - 1
    while x > 0:
        if not HashListArray1[x] or not HashListArray2[x]:
            x -= 1
            continue
        hashdict1, hashdict2 = {}, {}
        for i in HashListArray1[x]:
            num = 0
            for j in HashListArray2[x]:
                if i in delnode1 or j in delnode2:
                    continue
                if id2hash1[i] == id2hash2[j]:
                    num += 1
                    datanode.append((i, j, id2hash1[i]))
                    mov(delnode1, childrendict1, i)
                    mov(delnode2, childrendict2, j)
            if num:
                hashdict1[id2hash1[i]] = num
                hashdict2[id2hash1[i]] = hashdict2.get(id2hash1[i], 0) + 1
        for a in hashdict1:
            intersection += x * min(hashdict1[a], hashdict2[a])
        x -= 1
    union = len(id2hash1) + len(id2hash2) - intersection
    sim = float(intersection) / union if union else 0
    return sim
