import markdown, re, urllib.parse

valid_url_schemes =  ["https", "http"]
valid_url_special_chars = ["-", "_", "."]

def convert_to_html(mk):
    print("mk", mk)
    converted = remove_think(mk)
    converted = markdown.markdown(converted)
    converted = converted.replace("\n", "<br>")
    converted = converted.replace('"', "'")


    return converted

def check_link(link):
    parsed_link = urllib.parse.urlparse(link)

    if parsed_link.scheme in valid_url_schemes:
        pass
    else:
        return False

    if len(parsed_link.netloc) > 0:
        for char in parsed_link.netloc:
            if char.isalnum() or (char in valid_url_special_chars):
                continue
            else:
                return False
    else:
        return False

    return True


def remove_think(string):
    think_pattern = r"<think>(.|\n)*?</think>"
    new_string = re.sub(think_pattern, "", string)

    return new_string




