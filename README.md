# DNNCLone
This repository contains the core code description of the paper 《From Simple to Structural Clone in Neural Networks: Tapping the Data Flow Trace》

## DataConstruct

--github_get.py--
Download github's name and clone_url as well as creation time and update time through GitHub_api
All downloaded in github_get_final.csv

--github_rank.py--
The specific usage is criticality_score -depsdev-disable github_url. It can return a series of information github_rank.py can return the links with scores for all the repositories in a csv.

--github_get.py--
Currently, there are two key data: github_get_filter_final.csv contains the name, order and time of each warehouse. Through the full_name of the warehouse, you can access the corresponding folder, which corresponds to the specific warehouse content.

## GraphConstruct
