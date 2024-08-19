import os
import io
import re
import json
from ruamel.yaml import YAML
from github import Github, Auth
from parse_utils import *
from file_utils import *

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
repo_name = os.environ.get("REPO_NAME")
issue_number = int(os.environ.get("ISSUE_NUMBER"))

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(repo_name)
issue = repo.get_issue(number = issue_number)

# Parse issue
regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
data = dict(re.findall(regex, issue.body))

doi = data["-> doi"].strip()

# Verify doi is valid
# because we are usign reserved DOIs, they can't be verified usign http.
# instead, test if the DOI is in a sensible form
response = extract_doi_parts(doi)
if response != "No valid DOI found in the input string.":
    # Insert DOI into metadata

    # Read the RO-Crate  (JSON file)
    json_file_path = "ro-crate-metadata.json"
    with open(json_file_path, 'r') as file:
            rocrate = json.load(file)

    #add the DOI and any other chanages to the to the ro-crate

    key_path = "@graph../.identifier"
    create_or_update_json_entry(rocrate, key_path, doi)
    key_path = "@graph.model_inputs.identifier"
    create_or_update_json_entry(rocrate, key_path, doi)
    key_path = "@graph.model_outputs.identifier"
    create_or_update_json_entry(rocrate, key_path, doi)
    citation_str = format_citation(rocrate)
    key_path = "@graph../.creditText"
    create_or_update_json_entry(rocrate, key_path, citation_str)

    #save the updated crate
    metadata_out = json.dumps(rocrate, indent=4)
    file_content = repo.get_contents(json_file_path)
    commit_message = "Update ro-crate with DOI etc."
    repo.update_file(json_file_path, commit_message, metadata_out, file_content.sha)

    #add the creditText
    #json_data should be the updatated rocrate dictionary
    #citation_str = format_citation(json_data)
    #key_path = "@graph../.creditText"
    #json_data = create_or_update_json_entry(json_file_path, key_path, citation_str)
    #metadata_out = json.dumps(json_data, indent=4)
    #file_content = repo.get_contents(json_file_path)
    #commit_message = "Update ro-crate with DOI"
    #repo.update_file(json_file_path, commit_message, metadata_out, file_content.sha)

    #update the github cff file
    cff_text = ro_crate_to_cff(rocrate)
    cff_file_path = "CITATION.cff"
    file_content = repo.get_contents(cff_file_path)
    commit_message = "Update CITATION.cff"
    repo.update_file(cff_file_path, commit_message, cff_text, file_content.sha)


    #need to copy into the website materials folder
    web_json_file_path = ".website_material/ro-crate-metadata.json"
    file_content = repo.get_contents(web_json_file_path)
    commit_message = "Update Website ro-crate with DOI"
    repo.update_file(web_json_file_path, commit_message, metadata_out, file_content.sha)

    #update CSV
    csv_file_path = 'metadata_trail/nci_iso.csv'
    field = 'DOI (NCI Internal Field)'
    updated_csv_content = update_csv_content(csv_file_path, field, doi)
    file_content = repo.get_contents(csv_file_path)
    commit_message = "Update nci_iso.csv with DOI"
    repo.update_file(csv_file_path, commit_message, updated_csv_content, file_content.sha)

    # YAML
    yaml = YAML(typ=['rt', 'string'])
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Read existing file
    yaml_file_path = ".website_material/index.md"
    web_yaml_dict = read_yaml_with_header(yaml_file_path)

    # Path to key to update
    #key_path = "dataset.doi"
    #add doi to the top level only
    key_path = "doi"
    # Update value
    navigate_and_assign(web_yaml_dict, key_path, doi)
    key_path = "creditText"
    # Update value
    navigate_and_assign(web_yaml_dict, key_path, citation_str)

    # Use an in-memory text stream to hold the YAML content
    stream = io.StringIO()
    stream.write("---\n")
    yaml.dump(web_yaml_dict, stream)
    stream.write("---\n")
    yaml_content_with_frontmatter = stream.getvalue()

    file_content = repo.get_contents(yaml_file_path)
    commit_message = "Update YAML file with DOI"
    repo.update_file(yaml_file_path, commit_message, yaml_content_with_frontmatter, file_content.sha)

    # Print True to indicate success so that files may be copied to website repo
    print(True)
else:
    issue.create_comment(f"An error was encountered trying to access the DOI provided. Please check that it was entered correctly.\n{response}")
    issue.remove_from_labels("model published")
    # Print False to indicate failure so that files are not copied to website repo
    print(False)
