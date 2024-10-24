import os
from github import Github, Auth

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_owner = os.environ.get("REPO_OWNER")
repo_name = os.environ.get("REPO_NAME")
slug = os.environ.get("SLUG")

auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(f"{repo_owner}/{repo_name}")

phrase = 'Model repository created at' # Phrase to find the right comment


for issue in repo.get_issues():
    for comment in issue.get_comments():
        if phrase in comment.body:
            comment_slug = comment.body.split('ModelAtlasofTheEarth/')[1] # get slug in issue comment
            if slug == comment_slug:
                issue.add_to_labels('model published')
                break

        