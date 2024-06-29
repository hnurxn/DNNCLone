import os

def transform(file):
    with open(f"{file}","r") as f:
        lines = f.readlines()
        
    newlines = ""
    for line in lines:
        data = line.split(", ")
        unique_id1 = data[0]
        project_id1 = unique_id1.split("_")[0]
        node_id1 = unique_id1.split("_")[1]
        unique_id2 = data[1].split(":")[0]
        project_id2 = unique_id2.split("_")[0]
        node_id2 = unique_id2.split("_")[1]
        newlines+= f"{project_id1}:{node_id1}|{project_id2}:{node_id2}\n"
    return newlines

res = ""
for i in range(6):
    res+=transform(f"clone_results_gpu{str(i)}.txt")
    # res.append(transform(f"clone_results_gpu{str(i)}.txt"))

with open("CodeGemma.txt","w") as f:
    f.write(res)
