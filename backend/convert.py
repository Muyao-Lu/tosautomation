import markdown

def convert_to_html(mk):
    converted = markdown.markdown(mk)
    converted.replace("\n", "<br>")
    converted.replace('"', " ")
    return converted


