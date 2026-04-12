import ply.lex as lex
import sys

tokens = ("INCLUIR", "DEFINIR", "IDENTIFIER", "TEXT")


def preprocess(data):
    defines = {}
    buffer = ""
    memory = []
    loaded_files = {}

    def add_to_memory(name, text):
        words = text.split()
        start = len(memory)
        memory.extend(words)
        loaded_files[name] = (start, len(words))

    # Token: include
    def t_INCLUIR(t):
        r"%[ ]*include[ ]+[^\n]+"
        nonlocal buffer
        parts = t.value.split()
        filename = parts[-1]

        try:
            with open(filename, "r") as f:
                content = f.read()
            add_to_memory(filename, content)
            buffer += content
        except:
            print(f"Error: no se pudo abrir {filename}")

    def t_DEFINIR(t):
        r"%[ ]*define[ ]+[a-zA-Z_][a-zA-Z0-9_]*[ ]+[^\n]+"
        parts = t.value.split()
        name = parts[-2]
        value = parts[-1]
        defines[name] = value

    def t_IDENTIFIER(t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        nonlocal buffer
        buffer += t.value + " "

    def t_TEXT(t):
        r".|\n"
        nonlocal buffer
        buffer += t.value

    t_ignore = ""

    def t_error(t):
        t.lexer.skip(1)

    lexer = lex.lex()
    lexer.input(data)

    while lexer.token():
        pass

    result = buffer.split()
    for i, word in enumerate(result):
        if word in defines:
            result[i] = defines[word]

    return " ".join(result), loaded_files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python preprocessor.py <archivo>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, "r") as f:
            data = f.read()
    except:
        print(f"Error: no se pudo abrir {filename}")
        sys.exit(1)

    output, loaded = preprocess(data)
    print(output)
    print("\nLoaded files:")
    for name, (start, count) in loaded.items():
        print(f"  {name}: start={start}, count={count}")
