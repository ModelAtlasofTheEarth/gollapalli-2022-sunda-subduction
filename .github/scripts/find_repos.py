import os
import json
import requests
from github import Github, Auth

# Environment variables
token = os.environ.get("TOKEN")
repo_name = os.environ.get("REPO")
org = os.environ.get("ORG")

repos = []

# Get org
auth = Auth.Token(token)
g = Github(auth=auth)
org = g.get_organization(org)

# Find repos created from this template
for repo in org.get_repos():
    repo_json = requests.get(repo.url).json()
    if 'template_repository' in repo_json:
        if repo_json['template_repository']['name'] == repo_name:
            repos.append(repo.name)

print(json.dumps(repos))