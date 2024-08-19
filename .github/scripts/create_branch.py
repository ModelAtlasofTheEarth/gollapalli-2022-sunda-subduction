import os
from github import Github, Auth

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_owner = os.environ.get("REPO_OWNER")
repo_name = os.environ.get("REPO_NAME")
branch_name = os.environ.get("BRANCH_NAME")

auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(f"{repo_owner}/{repo_name}")

# Check if the branch name already exists
try:
    assert repo.get_git_ref(f"heads/{branch_name}").ref is not None
    print("Branch already exists")

# Create new branch if it doesn't
except:
    base_ref = repo.get_git_ref(f"heads/{repo.default_branch}")

    repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
