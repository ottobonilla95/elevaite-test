import os


# get file text from file
def readTextFile(path, char_encoding="utf-8"):
    if not path:
        return ""
    if not os.path.exists(path):
        return ""
    in_file = open(file=path, mode="r", encoding=char_encoding)
    text = in_file.read()
    in_file.close()
    return text


# save text to file
def saveTextFile(path, text, append=False):
    if not path or not text:
        return
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    wmode = "a" if append else "w"
    new_file = False if os.path.isfile(path) else True
    out_file = open(file=path, mode=wmode, encoding="utf-8")
    if wmode == "a" and not new_file:
        out_file.write("\n")
    out_file.write(text)
    out_file.close()


# search file/file with extension/file with text in a directory
def searchFile(path, name="*", extn="*", text="", char_encoding="utf-8"):
    file_paths = []
    if not path or not os.path.exists(path):
        return file_paths
    for root, dirs, files in os.walk(path):
        matches = []
        for file_name in files:
            if name == "*" and extn == "*":
                matches.append(file_name)
            elif name == "*" and file_name.endswith(extn):
                matches.append(file_name)
            elif extn == "*" and file_name.startswith(name):
                matches.append(file_name)
            elif file_name.startswith(name) and file_name.endswith(extn):
                matches.append(file_name)
        paths = [os.path.join(root, file_name) for file_name in matches]
        file_paths.extend(paths)
    if text:
        for fp in file_paths:
            if text not in readTextFile(fp, char_encoding):
                file_paths.remove(fp)
    return file_paths
