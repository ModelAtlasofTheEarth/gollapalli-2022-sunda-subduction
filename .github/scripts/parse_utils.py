import re
import yaml


def extract_doi_parts(doi_string):
    # Regular expression to match a DOI within a string or URL
    # It looks for a string starting with '10.' followed by any non-whitespace characters
    # and optionally includes common URL prefixes
    # the DOI
    doi_pattern = re.compile(r'(10\.[0-9]+/[^ \s]+)')

    # Search for DOI pattern in the input string
    match = doi_pattern.search(doi_string)

    # If a DOI is found in the string
    if match:
        # Extract the DOI
        doi = match.group(1)

        # Clean up the DOI by removing any trailing characters that are not part of a standard DOI
        # This includes common punctuation and whitespace that might be accidentally included
        #doi = re.sub(r'[\s,.:;]+$', '', doi)
        doi = re.sub(r'[\s,.:;|\/\?:@&=+\$,]+$', '', doi)

        # Split the DOI into prefix and suffix at the first "/"
        #prefix, suffix = doi.split('/', 1)

        return doi
    else:
        # Return an error message if no DOI is found
        return "No valid DOI found in the input string."


def format_citation(ro_crate):
    # Find the root entity (main dataset)
    root_entity = next((item for item in ro_crate['@graph'] if item['@id'] == './'), None)
    if not root_entity:
        return "Error: Root data entity not found."

    # Extract essential data: title, DOI, publication year
    title = root_entity.get('name', 'No title available')

    # Handle the case where 'identifier' might be an empty string or empty list
    identifier = root_entity.get('identifier')
    if isinstance(identifier, list):
        doi = identifier[0] if identifier and identifier[0] else 'No DOI available'
    elif isinstance(identifier, str) and identifier:
        doi = identifier
    else:
        doi = 'No DOI available'

    date_published = root_entity.get('datePublished', '')[:4]  # Extract the first four characters, which represent the year

    # Extract publisher information, handling multiple publishers
    publisher_ids = root_entity.get('publisher', [])
    if not isinstance(publisher_ids, list):
        publisher_ids = [publisher_ids]
    publishers = []
    for publisher_id in publisher_ids:
        publisher_entity = next((item for item in ro_crate['@graph'] if item['@id'] == publisher_id['@id']), None)
        if publisher_entity:
            publishers.append(publisher_entity.get('name', 'No publisher available'))
    publisher_names = ', '.join(publishers) if publishers else "No publisher available"

    # Extract and format author names
    authors = root_entity.get('creator', [])
    # If 'authors' is a dictionary (single author), convert it to a list for uniform handling
    if isinstance(authors, dict):
        authors = [authors
    author_names = []
    for author_id in authors:
        author_entity = next((item for item in ro_crate['@graph'] if item['@id'] == author_id['@id']), None)
        if author_entity:
            surname = author_entity.get('familyName', '')
            given_name_initial = author_entity.get('givenName', '')[0] if author_entity.get('givenName', '') else ''
            author_names.append(f"{surname}, {given_name_initial}.")

    # Join author names with commas, and use '&' before the last author if multiple
    if len(author_names) > 1:
        authors_formatted = ', '.join(author_names[:-1]) + f", & {author_names[-1]}"
    else:
        authors_formatted = ''.join(author_names)

    # Create formatted citation string
    citation = f"{authors_formatted} ({date_published}). {title} [Data set]. {publisher_names}. https://doi.org/{doi.split('/')[-1]}"
    return citation





def ro_crate_to_cff(ro_crate):
    # Find the root entity
    root_entity = next((item for item in ro_crate['@graph'] if item['@id'] == './'), None)
    if not root_entity:
        return "Error: Root data entity not found."

    # Extract necessary fields
    title = root_entity.get('name', 'No title available')
    version = root_entity.get('version', '1.0')
    doi = root_entity.get('identifier', ['No DOI available'])[0]
    date_released = root_entity.get('datePublished', '').split('T')[0]
    url = root_entity.get('url', 'No URL provided')

    # Extract authors
    authors = root_entity.get('creator', [])
    author_list = []
    for author_id in authors:
        author_entity = next((item for item in ro_crate['@graph'] if item['@id'] == author_id['@id']), None)
        if author_entity:
            author_list.append({
                'family-names': author_entity.get('familyName', ''),
                'given-names': author_entity.get('givenName', ''),
                'orcid': author_id['@id']
            })

    # Construct the CFF object
    cff_dict = {
        'cff-version': '1.2.0',
        'message': 'If you use this model, please cite it as below.',
        'authors': author_list,
        'title': title,
        'version': version,
        'doi': doi,  # Assuming DOI is a complete URL, extract just the number
        'date-released': date_released,
        'url': url,
        'type': 'dataset'
    }

    # Convert dict to YAML format
    cff_yaml = yaml.dump(cff_dict, sort_keys=False, default_flow_style=False)
    return cff_yaml
