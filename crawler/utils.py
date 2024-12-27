def deleteSubstrings(string, substrings):
    for str in substrings:
        string = string.replace(str, "")
    return string