import ply.lex as lex
import ply.yacc as yacc
from  pc.ram import RAM
import sys
import json
import os
import re

tokens = ("TEXTLABELS", "DATALABELS", "TEXTSEC", "DATASEC", "INT", "ID", "REF")

literals = [":", "{", "}", "\n"]

t_ignore = " \t"

def t_TEXTLABELS(t): r"TextLabels"; return t
def t_DATALABELS(t): r"DataLabels"; return t
def t_TEXTSEC(t): r"TextSection"; return t
def t_DATASEC(t): r"DataSection"; return t

def t_INT(t):
    r"0b[01]+|0x[0-9A-Fa-f]+|\d+"
    t.value = int(t.value, 0)
    return t

def t_ID(t):
    r"[A-Za-z_]\w*"
    return t

def t_REF(t):
    r"\{[A-Za-z_]\w*:[^}]+\}"
    # ejemplo: {A:0b111000}
    label, addr = t.value[1:-1].split(":")
    t.value = (label, int(addr, 0))
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

def t_error(t):
    print("Símbolo inesperado:", t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

def p_file(p):
    """file : sections"""
    p[0] = p[1]

def p_sections(p):
    """sections : section sections
                | section"""
    if len(p) == 3:
        result = {"text": [], "data": [], "labels": {}}
        result["text"] = p[1]["text"] + p[2]["text"]
        result["data"] = p[1]["data"] + p[2]["data"]
        result["labels"] = {**p[1]["labels"], **p[2]["labels"]}
        p[0] = result
    else:
        p[0] = p[1]


def p_section_text(p):
    """section : TEXTSEC ':' INT section_body"""
    p[0] = {"text": p[4], "data": [], "labels": {}}

def p_section_data(p):
    """section : DATASEC ':' INT section_body"""
    p[0] = {"text": [], "data": p[4], "labels": {}}

def p_section_labels(p):
    """section : TEXTLABELS '{' label_defs '}'
               | DATALABELS '{' label_defs '}'"""
    p[0] = {"text": [], "data": [], "labels": p[3]}

def p_label_defs(p):
    """label_defs : ID ':' INT label_defs
                  | ID ':' INT"""
    if len(p) == 4:
        p[0] = {p[1]: p[3]}
    else:
        d = {p[1]: p[3]}
        d.update(p[4])
        p[0] = d

def p_section_body(p):
    """section_body : word section_body
                    | word"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_word(p):
    """word : INT
            | REF"""
    p[0] = p[1]

def p_error(p):
    print("Error de sintaxis", p)

parser = yacc.yacc()

def link(files):
    text, data, labels = [], [], {}
    offset_text = 0

    for f in files:
        with open(f) as file:
            content = file.read()
        obj = parser.parse(content, lexer=lexer)

        # Ajustar etiquetas
        for lbl, addr in obj["labels"].items():
            labels[lbl] = addr + offset_text
        
        # Guardar secciones
        text.extend(obj["text"])
        data.extend(obj["data"])
        offset_text += len(obj["text"])

    return {"text": text, "data": data, "labels": labels}

def loader(linked, ram, base_addr=0):
    # Cargar instrucciones desde base_addr
    # Soporta referencias relativas en formato: INT seguido de REF
    # Ejemplo: 0x02{while_end:0x38} -> [0x02, ("while_end", 56)]
    resolved_text = []
    i = 0
    text_words = linked["text"]
    while i < len(text_words):
        word = text_words[i]

        if (
            isinstance(word, int)
            and i + 1 < len(text_words)
            and isinstance(text_words[i + 1], tuple)
        ):
            label, bits = text_words[i + 1]
            addr = linked["labels"][label]
            mask = (1 << bits) - 1
            combined = (word << bits) | (addr & mask)
            resolved_text.append(combined)
            i += 2
            continue

        if isinstance(word, tuple):  # referencia {label:bits} sin prefijo
            label, bits = word
            addr = linked["labels"][label]
            mask = (1 << bits) - 1
            word = addr & mask

        resolved_text.append(word)
        i += 1

    for i, word in enumerate(resolved_text):
        ram.request(word, base_addr + i, 1)  # MemWrite

    # Cargar datos después del texto
    base_data = base_addr + len(resolved_text)
    for i, word in enumerate(linked["data"]):
        ram.request(word, base_data + i, 1)

    # opcional: escribir PC en dirección base
    ram.request(base_addr, 0, 1) 
    return ram

# Diccionario
def export_labels(labels, filename="labels.json"):
    dict_out = {tag: f"{addr:064b}" for tag, addr in labels.items()}
    with open(filename, "w") as f:
        json.dump(dict_out, f, indent=2)
    print(f"Diccionario de etiquetas guardado en {filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m spl.linker_loader <archivos.o...> <salida.exe> [direccion_base]")
        sys.exit(1)

    files = sys.argv[1:-2] if len(sys.argv) > 3 else sys.argv[1:-1]
    out_file = sys.argv[-2] if len(sys.argv) > 3 else sys.argv[-1]
    base_addr = int(sys.argv[-1], 0) if len(sys.argv) > 3 else 0

    linked = link(files)

    # Exportar etiquetas a JSON
    dict_out = {tag: f"{addr+base_addr:064b}" for tag, addr in linked["labels"].items()}
    with open("labels.json", "w") as f:
        json.dump(dict_out, f, indent=2)
    print("Diccionario de etiquetas guardado en labels.json")

    ram = RAM(word_size="64", positions=2**16)
    loader(linked, ram, base_addr=base_addr)

    print(f"Ejecutable generado: {out_file}")
    print(f"Programa cargado desde dirección base {base_addr} (decimal) / {base_addr:064b} (binario)")
    print("Primeras posiciones de RAM:")
    for i in range(base_addr, base_addr+20):
        print(f"RAM[{i}] = {ram.request(0, i, 0)}")

