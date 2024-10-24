import os
import base64
from github import Github, Auth

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
source_repo_owner = os.environ.get("SOURCE_REPO_OWNER")
source_repo_name = os.environ.get("SOURCE_REPO_NAME")
source_path = os.environ.get("SOURCE_PATH")
target_repo_owner = os.environ.get("TARGET_REPO_OWNER")
target_repo_name = os.environ.get("TARGET_REPO_NAME")
target_branch_name = os.environ.get("TARGET_REPO_BRANCH")
target_path = os.environ.get("TARGET_PATH")

auth = Auth.Token(token)
g = Github(auth=auth)
source_repo = g.get_repo(f"{source_repo_owner}/{source_repo_name}")
target_repo = g.get_repo(f"{target_repo_owner}/{target_repo_name}")

def copy_files(contents, target_path):
    for content in contents:
        if content.type == "dir":
            # Get the contents of the directory and copy recursively
            copy_files(source_repo.get_contents(content.path), f"{target_path}/{content.name}")
        else:
            # Check if the file already exists in the target repo
            try:
                target_file = target_repo.get_contents(f"{target_path}/{content.name}", ref=target_branch_name)
                # File exists, compare contents
                if content.sha != target_file.sha:
                    # Contents differ, update the file
                    source_file_content = base64.b64decode(source_repo.get_git_blob(content.sha).content)
                    target_repo.update_file(f"{target_path}/{content.name}",f"Updating {content.name}", source_file_content, target_file.sha, branch=target_branch_name)
            except:
                # Copy file to target repository
                source_file_content = base64.b64decode(source_repo.get_git_blob(content.sha).content)
                target_repo.create_file(f"{target_path}/{content.name}", f"Copying {content.name}", source_file_content, branch=target_branch_name)

# Get contents of source directory
source_contents = source_repo.get_contents(source_path)

# Start copying files
copy_files(source_contents, target_path)
