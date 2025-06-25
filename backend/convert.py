
def convert_to_html(text: str) -> str:
    t = text.replace("`", "")
    t = t.replace("html", "")
    t = t.replace("\n", "<br>")
    r = 0
    rems = 0
    for i in range(len(t)):
        r = round(r, 5)
        if t[i- rems*4:i- rems*4+4] == "<br>":
            if r > 0:
                t = t[:i - rems*4] + t[i- rems*4+4:]
                r = 1
                rems += 1
            else:
                r = 1
        else:
            if r > 0:
                r -= 0.2
            else:
                r = 0

    return t
