import csv
from io import StringIO

def update_csv_content(file_path, field, value):
    """
    Read a two-column CSV file and update (or append) the row where row[0] == field.

    Parameters:
    - file_path (str): Path to the CSV file on disk.
    - field (str): The value in the first column to match.
    - value (str): The new value to set in the second column.

    Returns:
    The full updated CSV as a string. The caller is responsible for writing
    this string back to disk or committing it via the GitHub API.
    """
    updated_rows = []
    field_exists = False

    with open(file_path, mode="r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == field:
                row[1] = value
                field_exists = True
            updated_rows.append(row)

    if not field_exists:
        updated_rows.append([field, value])

    updated_csv_content = StringIO()
    writer = csv.writer(updated_csv_content)
    writer.writerows(updated_rows)

    return updated_csv_content.getvalue()
