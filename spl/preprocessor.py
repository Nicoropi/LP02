import ply.lex as lex
import sys

tokens = ( 'INCLUIR', 'DEFINIR', 'IDENTIFIER', 'TEXT' )

def preprocess(data):
    defines = {}
    buffer = ""

    #====================================#
    #               Tokens               #
    #====================================#
    def t_INCLUIR(t):
        r'%[ ]*include[ ]+[^\n]+'
        parts = t.value.split()
        filename = parts[-1]

        try:
            with open(filename, 'r') as f:
                nonlocal buffer
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
        nonlocal buffer
        buffer += t.value + " "

    def t_TEXT(t):
        r'.|\n'
        nonlocal buffer
        buffer += t.value

    t_ignore = ''

    def t_error(t):
        t.lexer.skip(1)

    #====================================#
    #                Lexer               #
    #====================================#
    lexer = lex.lex()
    lexer.input(data)

    #====================================#
    #              Ejecucion             #
    #====================================#
    while lexer.token():
        pass

    result = []
    for word in buffer.split():
        if word in defines:
            result.append(defines[word])
        else:
            result.append(word)

    return " ".join(result)


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