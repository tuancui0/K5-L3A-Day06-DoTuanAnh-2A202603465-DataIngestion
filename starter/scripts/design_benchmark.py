import json

with open("data/corpus.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)

pages_by_num = {p["page"]: p for p in corpus}

def find_snippet(page_num, keyword):
    p = pages_by_num.get(page_num)
    if not p:
        return None
    text = p["text"]
    idx = text.lower().find(keyword.lower())
    if idx != -1:
        start = max(0, idx - 80)
        end = min(len(text), idx + 200)
        return text[start:end]
    return None

keywords_to_check = [
    (1, "Guido van Rossum"),
    (2, "end="),
    (3, "case-sensitive"),
    (4, "concatenation"),
    (5, "scientific notation"),
    (6, "syntax error"),
    (7, "#"),
    (8, "open-source"),
    (11, "int("),
    (13, "floating-point"),
    (14, "floor division"),
    (15, "math.sqrt"),
    (16, "PEP 8"),
    (19, "Boolean"),
    (20, "indentation"),
    (21, "short-circuit"),
    (22, "precedence"),
    (23, "elif"),
    (26, "infinite loop"),
    (27, "range("),
    (29, "break"),
    (30, "else"),
    (32, "def"),
    (34, "global"),
    (35, "default parameter")
]

for page, kw in keywords_to_check:
    res = find_snippet(page, kw)
    if res:
        print(f"Page {page:02d} [{kw}]: Found!")
    else:
        print(f"Page {page:02d} [{kw}]: NOT FOUND!")

