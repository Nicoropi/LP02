import ply.lex as lex
import sys

defines = {}
buffer = ""

#====================================#
#               Tokens               #
#====================================#
tokens = (
    'INCLUIR',
    'DEFINIR',
    'IDENTIFIER',
    'TEXT'
)

#====================================#
#               Reglas               #
#====================================#
def t_INCLUIR(t):
    r'%[ ]*include[ ]+[^\n]+'
    global buffer

    parts = t.value.split()
    filename = parts[-1]

    try:
        with open(filename, 'r') as f:
            buffer += f.read()
    except:
        print(f"Error: no se pudo abrir {filename}")

def t_DEFINIR(t):
    r'%[ ]*define[ ]+[a-zA-Z_][a-zA-Z0-9_]*[ ]+[^\n]+'
    parts = t.value.split()

    name = parts[-2]
    value = parts[-1]

    defines[name] = value

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    global buffer
    buffer += t.value + " "

def t_TEXT(t):
    r'.|\n'
    global buffer
    buffer += t.value

t_ignore = ''

def t_error(t):
    print(f"Caracter ilegal: {t.value[0]}")
    t.lexer.skip(1)

# =========================
# Construcción del lexer
# =========================
lexer = lex.lex()

# =========================
# Ejecución
# =========================
def preprocess(data):
    global buffer
    buffer = ""

    lexer.input(data)

    # Primero, obtiene los Definir e incluye archivos
    while lexer.token():
        pass

    # Despues, reemplaza los defines
    result = []
    for word in buffer.split():
        if word in defines:
            result.append(defines[word])
        else:
            result.append(word)

    return " ".join(result)


# =========================
# MAIN
# =========================
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

    output = preprocess(data)
    print(output)