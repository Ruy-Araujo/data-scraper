import os
import json


def save_file(path, filename, blob):
    if not os.path.isdir(path):
        os.makedirs(path)

    if blob["extension"] == 'json':
        with open(f"{path}/{filename}.json", "w", encoding="utf-8") as file:
            json.dump(blob, file, indent=2, ensure_ascii=False)

    elif blob["extension"] == 'pdf':
        with open(f"{path}/{filename}.pdf", "wb") as file:
            file.write(blob["data"])

    elif blob["extension"] == "zip":
        with open(f"{path}/{filename}.zip", "wb") as file:
            for chunk in blob["data"].iter_content(chunk_size=128):
                file.write(chunk)


def create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)
