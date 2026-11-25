import os
import re
import json
from github import Github, Auth
from rocrate.rocrate import ROCrate
from parse_utils import extract_doi_parts, format_citation, ro_crate_to_cff, normalize_rocrate_dict
from file_utils import update_csv_content

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_name = os.environ.get("REPO_NAME")
issue_number = int(os.environ.get("ISSUE_NUMBER"))
update_website_material = os.environ.get("UPDATE_WEBSITE_MATERIAL", "True").lower() in ("true", "1", "yes")

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(repo_name)
issue = repo.get_issue(number=issue_number)

# Parse issue body into key-value pairs
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
data = dict(re.findall(regex, issue.body))

doi = data["-> doi"].strip()

# Verify DOI is in a sensible form.
# Reserved DOIs cannot be verified via HTTP so we only validate the format.
response = extract_doi_parts(doi)
if response != "No valid DOI found in the input string.":
    canonical_doi = f"https://doi.org/{response}"

    # --- Load RO-Crate from repo ---
    json_file_path = "ro-crate-metadata.json"
    file_content = repo.get_contents(json_file_path)
    rocrate_dict = json.loads(file_content.decoded_content.decode("utf-8"))
    rocrate_dict = normalize_rocrate_dict(rocrate_dict)

    # Load into rocrate library (detached crate from raw dict)
    crate = ROCrate(rocrate_dict)

    # --- Update identifiers ---
    root = crate.root_dataset
    root["identifier"] = [canonical_doi]

    for entity_id in ("model_outputs", "model_output_data"):
        entity = crate.dereference(entity_id)
        if entity is not None:
            entity["identifier"] = [canonical_doi]

    # --- Update creditText ---
    citation_str = format_citation(crate)
    root["creditText"] = citation_str

    # --- Serialize and commit ro-crate-metadata.json ---
    metadata_out = json.dumps(crate.metadata.generate(), indent=4)
    commit_message = "Update ro-crate-metadata.json with DOI"
    repo.update_file(json_file_path, commit_message, metadata_out, file_content.sha)

    # --- Generate and commit CITATION.cff ---
    cff_text = ro_crate_to_cff(crate)
    cff_file_path = "CITATION.cff"
    cff_content = repo.get_contents(cff_file_path)
    commit_message = "Update CITATION.cff"
    repo.update_file(cff_file_path, commit_message, cff_text, cff_content.sha)

    # --- Update nci_iso.csv ---
    csv_file_path = ".metadata_trail/nci_iso.csv"
    field = "DOI (NCI Internal Field)"
    updated_csv_content = update_csv_content(csv_file_path, field, doi)
    csv_content = repo.get_contents(csv_file_path)
    commit_message = "Update nci_iso.csv with DOI"
    repo.update_file(csv_file_path, commit_message, updated_csv_content, csv_content.sha)

    # Print True to indicate success so that files may be copied to website repo
    print(True)

else:
    issue.create_comment(
        f"An error was encountered trying to access the DOI provided. "
        f"Please check that it was entered correctly.\n{response}"
    )
    issue.remove_from_labels("model published")
    # Print False to indicate failure so that files are not copied to website repo
    print(False)
