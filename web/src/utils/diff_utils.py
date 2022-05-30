def get_file_content(path):
    with open(path, encoding="utf-8") as file:
        return file.readlines()
