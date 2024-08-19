import os
import json
from github import Github, Auth

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_owner = os.environ.get("REPO_OWNER")
repo_name = os.environ.get("REPO_NAME")
pr_title = os.environ.get("PR_TITLE")
event_path = os.environ.get("GITHUB_EVENT_PATH")
head_branch = os.environ.get("HEAD_BRANCH")
base_branch = os.environ.get("BASE_BRANCH")

def get_commit_messages(event_path):
    with open(event_path) as f:
        event_data = json.load(f)

    # Extract commits from event data
    commits = event_data['commits']

    # Extract commit messages
    commit_messages = '\n'.join(['- '+ commit['message'] for commit in commits])

    return commit_messages


# Get repo
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(f"{repo_owner}/{repo_name}")

# Generate PR body from commit messages in event json data:
pr_body = get_commit_messages(event_path)

# Existing PRs
existing_prs = repo.get_pulls(state='open', sort='created', base='main')

pr_exists = False

for pr in existing_prs:
    if pr.title == pr_title:
        pr_exists = True
        existing_pr = pr

        # Edit existing PR
        existing_pr_body = existing_pr.body
        updated_pr_body = existing_pr_body + '\n' + pr_body
        existing_pr.edit(body=updated_pr_body)

        print(f"Pull request body updated: {existing_pr.html_url}")
        break
    
if pr_exists == False:
    # Make new pull request
    new_pr = repo.create_pull(
        title = pr_title,
        body = "*Commits*\n\n" + pr_body,
        head = head_branch,
        base = base_branch
    )

    print(f"Pull request created: {new_pr.html_url}")

    