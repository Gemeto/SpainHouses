def deleteSubstrings(string, substrings):
    for str in substrings:
        string = string.replace(str, "")
    return string

def getLocationParsedComponent(location_data, component):
    if "response" in location_data:
        index = next((x for i, x in enumerate(location_data["response"]) if "label" in location_data["response"][x] and component in location_data["response"][x]["label"]), None)
        if index is not None:
            return location_data["response"][index]["value"]
    return None