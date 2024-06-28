# DNNCLone
This repository contains the core code description of the paper "From Simple to Structural Clone in Neural Networks: Tapping the Data Flow Trace."

There are four steps:
- Download the dataset
- Clean the dataset
- Construct the call graph
- Clone analysis

## DataSetDownload
First, between the dates 2012-04-01 and 2024-04-01, scrape all repositories with the keyword "pytorch" primarily in Python, including [full_name, clone_url, stargazers_count, topics, description, created_at, updated_at]. Due to the large number of repositories, slice scraping is required. After scraping, download the repository content in bulk according to the clone_url. The core code is as follows:

**--github_get.py--**

Replace 'token YOURTOKEN' in the headers dictionary with your valid GitHub token.
Change the CSV file path to your own path.
If needed, modify the params_base dictionary to change the search parameters. Adjust the start_date and stop_date variables to set the desired date range for repository creation dates.

--git_download--
Clone specific file types from GitHub repositories.
This tutorial shows how to use a Python script to clone specific file types (such as `.py` and `.pth` files) from GitHub repositories and execute in a multithreaded environment.

#### The script includes the following main functions:

1. **sanitize_folder_name(name)**: Cleans folder names by replacing `/` with `:`.
2. **get_repo_size(clone_url, token)**: Gets the size of the repository (in MB).
3. **get_default_branch(clone_url, token)**: Gets the default branch of the repository.
4. **log_constraints(clone_url, status_code, message)**: Logs request constraints.
5. **sparse_clone(order, name, clone_url, base_dir, token, pth_log)**: Uses sparse checkout to clone only `.py` and `.pth` files.
6. **process_repository(row, token, base_dir, pth_log)**: Processes each repository and decides whether to perform sparse clone based on the size.
7. **main()**: Main function, reads the CSV file, and processes each repository using multithreading.

#### Usage Steps

1. Replace `YOURPATH` in the script with the actual path, and `YOURTOKEN` with your GitHub token.

2. **Create the necessary directories and files**:
   - Repository directory: `repositories`
   - Log files: `contain_pth.csv` and `constraints.log`
   - CSV file: `github_get.csv`, containing columns `order`, `name`, and `clone_url`.

## DataSetPreprocessing

First, filter all repositories, removing those that do not contain `.py` files. Then, save the filtered repository links to a new CSV file. Using the widely-used `criticality_score` tool, score all the repositories in the CSV file, and obtain the top n repository links based on the scores. The core code is as follows:

**--github_rank--**
The specific usage is `criticality_score -depsdev-disable github_url`. This can return a series of information, and `github_rank.py` can return the links with scores for all the repositories in a CSV file. This calculates the criticality score of GitHub repositories. Here's how to use a Python script to calculate the criticality score of GitHub repositories and save the results to a CSV file.

#### The script includes the following main functions:

1. **get_criticality_score(repo_url)**: Gets the repository's criticality score by calling the `criticality_score` tool.
2. **process_repositories(csv_input, csv_output)**: Processes repository links in a CSV file, calculates the criticality score for each repository, and saves the results to a new CSV file.

#### Usage Steps

1. **Prepare the environment**:
   - Ensure the `criticality_score` tool is installed and configured.
   - Prepare the input CSV file `inputs.csv`, containing the column `Repository Link`.

2. **Run the script**:
   - Save the following code as `criticality_score_script.py`.
   - Ensure the input CSV file `inputs.csv` is in the script directory.
   - Run the script:
     ```sh
     python criticality_score_script.py
     ```

3. **View the results**:
   - The output file `scores.csv` will contain the score for each repository.


## GraphConstruct

Overview of Extracting and Analyzing Neural Network Modules.

1. **extract.py**
   - **Purpose:** Analyzes Python projects to extract neural network (NN) modules.
   - **Key Functions:**
     - **Class Transformers:** Remove constants and print statements.
     - **Code Analysis:** Parse and clean code, extract class definitions.
     - **Directory Processing:** Count lines of code, get directory size.
     - **Main Workflow:** Process repositories, extract NN modules, save results in JSON.

2. **dependency.py**
   - **Purpose:** Establishes dependencies between extracted NN modules.
   - **Key Functions:**
     - **`CodeVisitor`:** AST visitor to detect class calls.
     - **Dependency Setup:** Parse code to identify and set dependencies among NN modules.

3. **utils.py**
   - **Purpose:** Provides utility functions to support `extract.py` and `dependency.py`.
   - **Key Functions:**
     - **Command Execution:** Run shell commands.
     - **Dependency Management:** Build and translate dependency dictionaries, locate callee indices.

#### Usage Steps

1. **Setup:**
   - Place `extract.py`, `dependency.py`, and `utils.py` in the same directory.
   - Ensure you have a directory of Python projects to analyze.

2. **Run the Script:**
   - Execute `extract.py`:
     ```bash
     python extract.py
     ```

3. **Analyze Results:**
   - JSON files will be created in the specified storage folder, containing information about NN modules and their dependencies.


## CloneDetection