import os
from github import Github, Auth

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_name = os.environ.get("REPO_NAME")

# Get repo
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(repo_name)

# Find if any of the issues has the published label
published = False

for issue in repo.get_issues():
    for label in issue.labels:
        if 'published' in label.name:
            published = True

print(published)
