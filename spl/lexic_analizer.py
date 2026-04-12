import ply.lex as lex

tokens = (
    "IDENTIFIER",
    "NUMBER",
    "STRING",
    "EQ",
    "NE",
    "GT",
    "LT",
    "GE",
    "LE",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIV",
    "INC",
    "DEC",
    "COLON",
    "COMMA",
    "LBRACKET",
    "RBRACKET",
    "LPAREN",
    "RPAREN",
    "NEWLINE",
    "ASSIGN",
    "LET",
    "IF",
    "ELSE",
    "WHILE",
    "AND",
    "OR",
    "NOT",
    "TRUE",
    "FALSE",
    "PUSH",
    "GET",
)

reserved = {
    "let": "LET",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "true": "TRUE",
    "false": "FALSE",
    "push": "PUSH",
    "get": "GET",
}

t_ignore = " \t"


def t_IDENTIFIER(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "IDENTIFIER")
    return t


def t_NUMBER(t):
    r"(\d+\.\d+|\d+)"
    t.value = float(t.value) if "." in t.value else int(t.value)
    return t


def t_STRING(t):
    r"\"[^\"]*\"|'[^']*'"
    return t


def t_EQ(t):
    r"=="
    return t


def t_NE(t):
    r"!="
    return t


def t_GE(t):
    r">="
    return t


def t_LE(t):
    r"<="
    return t


def t_GT(t):
    r">"
    return t


def t_LT(t):
    r"<"
    return t


def t_PLUS(t):
    r"\+"
    return t


def t_MINUS(t):
    r"-"
    return t


def t_TIMES(t):
    r"\*"
    return t


def t_DIV(t):
    r"/"
    return t


def t_INC(t):
    r"\+\+"
    return t


def t_DEC(t):
    r"--"
    return t


def t_COLON(t):
    r":"
    return t


def t_COMMA(t):
    r","
    return t


def t_LBRACKET(t):
    r"\["
    return t


def t_RBRACKET(t):
    r"\]"
    return t


def t_LPAREN(t):
    r"\("
    return t


def t_RPAREN(t):
    r"\)"
    return t


def t_ASSIGN(t):
    r"="
    return t


def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    return t


def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)


def t_comment(t):
    r"\#.*"
    t.lexer.lineno += t.value.count("\n")
    pass


lexer = lex.lex()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python lexer.py <source_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = f.read()

    lexer.input(data)
    for tok in lexer:
        print(f"{tok.type:10} {tok.value}")
