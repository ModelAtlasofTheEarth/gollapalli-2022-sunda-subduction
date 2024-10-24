import json
from ruamel.yaml import YAML
import csv
import os
from io import StringIO

def create_or_update_json_entry(rocrate, keys_path, new_value):
    """
    Create or update a nested JSON entry in a ro-crate structure.

    Args:
        rocrate (dict): The main ro-crate dictionary.
        keys_path (str): Dot-separated path to the key that needs updating.
        new_value (any): New value to be inserted or updated.
    """
    # Split the keys path into individual components
    keys = keys_path.split('.')
    prefix = ""
    structure = rocrate

    # Traverse through the nested structure using keys except the last one
    for key in keys[:-1]:
        key = prefix + key

        # Handle potential './' prefix logic
        if key == "":
            prefix = "."
            continue
        else:
            prefix = ""

        if isinstance(structure, list):
            # Find the item with matching '@id' key
            for item in structure:
                if item.get("@id") == key:
                    structure = item
                    break
            else:
                print(f"Key '{key}' not found.")
                return
        elif key in structure:
            structure = structure[key]
        else:
            print(f"Key '{key}' not found.")
            return

    # The final key where the new value should be placed
    last_key = keys[-1]

    # Update the value at the final key
    if last_key in structure:
        if isinstance(structure[last_key], list):
            # Prepend only if the new value is not already in the list
            if new_value not in structure[last_key]:
                structure[last_key].insert(0, new_value)
        else:
            # Convert existing non-list value to a list if needed
            structure[last_key] = [new_value, structure[last_key]]
    else:
        # If the key doesn't exist, create a new list with the new value
        structure[last_key] = [new_value]


def navigate_and_assign(source, path, value):
    """Navigate through a nested dictionary and assign a value to the specified path."""
    keys = path.split('.')
    for i, key in enumerate(keys[:-1]):
        if key.isdigit():  # If the key is a digit, it's an index for a list
            key = int(key)
            while len(source) <= key:  # Extend the list if necessary
                source.append({})
            source = source[key]
        else:
            if i < len(keys) - 2 and keys[i + 1].isdigit():  # Next key is a digit, so ensure this key leads to a list
                source = source.setdefault(key, [])
            else:  # Otherwise, it leads to a dictionary
                source = source.setdefault(key, {})
    # Assign the value to the final key
    if keys[-1].isdigit():  # If the final key is a digit, it's an index for a list
        key = int(keys[-1])
        while len(source) <= key:  # Extend the list if necessary
            source.append(None)
        source[key] = value
    else:
        source[keys[-1]] = value


def read_yaml_with_header(file_path):
    """
    Read YAML content inside YAML header delimiters '---'
    """

    with open(file_path,'r') as file:
        data = file.read()

    yaml = YAML()
    yaml_content = yaml.load(data.strip('---\n'))

    return yaml_content

def update_csv_content(file_path, field, value):
    # Read the CSV file and update the field value
    updated_rows = []
    field_exists = False
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == field:
                row[1] = value
                field_exists = True
            updated_rows.append(row)

    # If the field does not exist, add a new line
    if not field_exists:
        updated_rows.append([field, value])

    # Convert the updated rows back into a CSV-formatted string
    updated_csv_content = StringIO()
    writer = csv.writer(updated_csv_content)
    writer.writerows(updated_rows)
    updated_csv_string = updated_csv_content.getvalue()

    return updated_csv_string
