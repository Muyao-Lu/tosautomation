import markdown

def convert_to_html(mk):
    converted = markdown.markdown(mk)
    converted = converted.replace("\n", "<br>")
    converted = converted.replace("\"", " ")
    return converted

