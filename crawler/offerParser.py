def parseFeature(features, feature_name):
    index = next((i for i, x in enumerate(features) if feature_name in x), None)
    if index is not None:
        return features[index]
    return None

def parseFeatureCss(features, feature_name, feature_name_selector, feature_value_selector):
    index = next((i for i, x in enumerate(features) if feature_name in x.css(feature_name_selector).get()), None)
    if index is not None:
        return features[index].css(feature_value_selector).get()
    return None

def parseGeocodifyLocationComponents(location_data, component):
    if "response" in location_data:
        index = next(
            (x for i, x in enumerate(location_data["response"]) if "label" in location_data["response"][x] and component in location_data["response"][x]["label"]), 
            None
        )
        if index is not None:
            return location_data["response"][index]["value"]
    return None

def deleteSubstrings(string, substrings):
    for str in substrings:
        string = string.replace(str, "")
    return string