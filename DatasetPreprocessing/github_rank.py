
import subprocess
import pandas as pd

def get_criticality_score(repo_url):
    try:

        result = subprocess.run(
            ['criticality_score', '-depsdev-disable', repo_url],
            capture_output=True, text=True
        )
        output = result.stdout
        

        score_line = [line for line in output.split('\n') if 'default_score' in line]
        if score_line:
            score = score_line[0].split(': ')[1]
            return score
        else:
            return "No Score Found"
    except Exception as e:
        return f"Error: {str(e)}"

def process_repositories(csv_input, csv_output):

    df = pd.read_csv(csv_input)

    df['Score'] = df['Repository Link'].apply(get_criticality_score)
    

    df.to_csv(csv_output, index=False)

input_csv = 'inputs.csv'  
output_csv = 'scores.csv'

process_repositories(input_csv, output_csv)
