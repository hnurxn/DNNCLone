import json
import os
import tokenize
import io
import keyword
from collections import defaultdict
import mmh3
import argparse
import autopep8
import time
from tqdm import tqdm
import re

def remove_whitespace(source_code):
    # Remove all whitespace characters, including spaces, tabs, and newlines
    cleaned_code = re.sub(r'\s+', '', source_code)
    return cleaned_code

argparser = argparse.ArgumentParser()
argparser.add_argument("--forestDir", type=str, default="/bdata2/AISystemEvaluation/DNNForest/")
argparser.add_argument("--outputDir", type=str, default="/bdata2/AISystemEvaluation/DNNForest/")
argparser.add_argument("--type", type=str)

args = argparser.parse_args()
inputdir = args.forestDir
clonetype = args.type

def format_code(code):
    formatted_code = autopep8.fix_code(code)
    return formatted_code

def label_node(node, child_nodeList):
    if node["Id"] not in child_nodeList:
        return "root"
    elif not node["Child_node"]:
        return "leaf"
    else:
        return "branch"

def calClonePairType(indexList, nodeTypeList):
    TypeNum = [0, 0, 0]  # root, leave, branch - count of each node type in the cluster
    
    for i in range(len(indexList)):
        if nodeTypeList[indexList[i]] == "root":
            TypeNum[0] += 1
        elif nodeTypeList[indexList[i]] == "leaf":
            TypeNum[1] += 1
        else:
            TypeNum[2] += 1
    clonePairTypeNum = [0, 0, 0, 0]  # roots, leaves, branches, others
    clonePairTypeNum[0] = int(TypeNum[0] * (TypeNum[0] - 1) / 2)
    clonePairTypeNum[1] = int(TypeNum[1] * (TypeNum[1] - 1) / 2)
    clonePairTypeNum[2] = int(TypeNum[2] * (TypeNum[2] - 1) / 2)
    clonePairTypeNum[3] = int(len(indexList) * (len(indexList) - 1) / 2) - clonePairTypeNum[0] - clonePairTypeNum[1] - clonePairTypeNum[2]
    return clonePairTypeNum

def extract_code_from_json(json_data):
    code_dict = {}
    project_id = json_data["Project_id"]
    for item in json_data["Forest"]:
        unique_id = f"{project_id}_{item['Id']}"
        code_dict[unique_id] = item["Code"]
    return code_dict

def T1_CloneDetection(codeIDList, pathList, codeList, nodeTypeList, ProjectIDList, zeroForestNum):
    tokenList = []
    for i in tqdm(range(len(codeList)), desc="Tokenize Code", unit="code"):
        tokenList.append(remove_whitespace(codeList[i]))
    T1Clusters = Cluster(codeIDList, tokenList)
    T1ClustersList = list(T1Clusters.values())
    
    buffer = io.StringIO()

    T1totalNum = 0
    T1totalInter = 0
    T1CloneNodeNum = 0
    allProjectIDCount = defaultdict(int)
    totalClonePairTypeNum = [0, 0, 0, 0]  # roots, leaves, branches, others
    i = 0
    
    for c in T1ClustersList:
        classNum = len(c)
        if classNum >= 2:
            ProjectIDCount = defaultdict(int)
            T1CloneNodeNum += classNum
            i += 1
            indexList = [item[1] for item in c]
            clonePairTypeNum = calClonePairType(indexList, nodeTypeList)
            for j in range(len(clonePairTypeNum)):
                totalClonePairTypeNum[j] += clonePairTypeNum[j]
            cloneIDText = ""  # Save cloneID and path
            for ID, index in c:
                cloneIDText += ID + " " + nodeTypeList[index] + " " + pathList[index] + "\n"
                ProjectID = ID.split(":")[0]
                ProjectIDCount[ProjectID] += 1
                allProjectIDCount[ProjectID] += 1

            # Statistics for each class
            cloneNum = int(classNum * (classNum - 1) / 2)
            inter = 0
            for n in ProjectIDCount.values():
                inter += int(n * (n - 1) / 2)
            intra = cloneNum - inter
            T1totalNum += cloneNum
            T1totalInter += inter

            codeEg = codeList[c[0][1]]  # Save code example

            # Write class information
            buffer.write("************************************************************************\n")
            buffer.write(f"Class {i}:\n")
            buffer.write(f"Class size: {classNum}\n")
            buffer.write(f"PairsNum: {cloneNum}\n")
            buffer.write(f"InterProjectPairsNum: {inter}\n")
            buffer.write(f"IntraProjectPairsNum: {intra}\n")
            buffer.write("Code example:\n")
            buffer.write("------------------------------------------------------------------------\n")
            buffer.write(f"{codeEg}\n")
            buffer.write("------------------------------------------------------------------------\n")
            buffer.write("Project:CodeID&Path:\n")
            buffer.write(cloneIDText)
            buffer.write("************************************************************************\n")

    # Statistical information
    T1totalIntra = T1totalNum - T1totalInter
    T1CloneRate = T1CloneNodeNum / len(codeIDList)
    allProjectCloneRate = round(len(allProjectIDCount) / (len(ProjectIDList) - zeroForestNum), 3)
    cloneTypeRate = [round(totalClonePairTypeNum[i] / T1totalNum, 3) for i in range(4)]

    # Write statistical information to file
    statistics = (
        f"TotalNum: {T1totalNum}\n"
        f"TotalInter: {T1totalInter}\n"
        f"TotalIntra: {T1totalIntra}\n"
        f"T1CloneRate: {T1CloneRate}\n"
        f"ProjectCloneRate: {allProjectCloneRate}\n"
        "CloneNodeType:\n"
        f"\tRoot: {totalClonePairTypeNum[0]} {cloneTypeRate[0]}\n"
        f"\tLeaf: {totalClonePairTypeNum[1]} {cloneTypeRate[1]}\n"
        f"\tBranch: {totalClonePairTypeNum[2]} {cloneTypeRate[2]}\n"
        f"\tOther: {totalClonePairTypeNum[3]} {cloneTypeRate[3]}\n"
        f"ClassNum: {i}\n"
    )

    with open(f"../results/T{clonetype}Clusters100.txt", 'w') as f:
        f.write(statistics)
        f.write(buffer.getvalue())

def cloneDetector(forestDir):
    forestPathList = [file for file in os.listdir(forestDir) if file.endswith('.json')]

    codeIDList = []
    pathList = []
    codeList = []
    nodeTypeList = []
    ProjectIDList = []
    zeroForestNum = 0
    time1 = time.time()
    for forestPath in tqdm(forestPathList, desc="Processing JSON files", unit="file"):
        try:
            fullPath = os.path.join(forestDir, forestPath)
            with open(fullPath, 'r') as f:
                forest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in file {fullPath}: {e}")
            continue
        except Exception as e:
            print(f"Error reading file {fullPath}: {e}")
            continue

        nodeList = forest.get("Forest", [])
        ProjectIDList.append(forest.get("Project_id", "Unknown"))
        
        if nodeList:
            allChildNodeList = sum((n.get("Child_node", []) for n in nodeList), [])
            for node in nodeList:
                codeIDList.append(f"{forest.get('Project_id', 'Unknown')}:{node.get('Id', 'Unknown')}")
                pathParts = node.get("File_path", "").split("/")
                modelpath = "/".join(pathParts[4:])
                pathList.append(modelpath)
                codeList.append(node.get("Code", ""))
                nodeTypeList.append(label_node(node, allChildNodeList))
        else:
            zeroForestNum += 1
    
    print("zeroForestNum: " + str(zeroForestNum))
    print("allNodeNum: " + str(len(codeIDList)))
    print("averageNodeNum: " + str(len(codeIDList)/(len(forestPathList)-zeroForestNum)))
    time2 = time.time()

    T1_CloneDetection(codeIDList, pathList, codeList, nodeTypeList, ProjectIDList, zeroForestNum)
    time3 = time.time()
    parse_time = int(time2 - time1)
    cluster_time = int(time3 - time2)
    print(f"Parse Time: {parse_time}, Cluster Time: {cluster_time}")
    return
  
def Cluster(codeIDList, tokenList):
    clusters = defaultdict(list)
    for i in range(len(codeIDList)):
        clusters[hash_code(tokenList[i])].append((codeIDList[i], i))
    return clusters

def hash_code(code):
    return mmh3.hash(code)

cloneDetector(f"/bdata2/AISystemEvaluation/DNNForest_{clonetype}/")
