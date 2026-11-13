import json

corpus = json.load(open('data/corpus.json', 'r', encoding='utf-8'))
pages = {p['page']: p for p in corpus}

def inspect_page(num):
    p = pages[num]
    print(f"=== PAGE {num}: {p['chapter']} - {p['title']} ===")
    for sec in p['sections']:
        print(f"--- Heading: {sec['heading']} ---")
        for idx, para in enumerate(sec['paragraphs']):
            print(f"[{idx}] {para[:150]}...")

# Inspect a selection of pages for dev and test questions
for pnum in [2, 3, 4, 6, 7, 11, 14, 15, 16, 20, 21, 23, 27, 29, 30, 32, 34, 35]:
    inspect_page(pnum)

