import ply.lex as lex

class Lexer:
    # TOKENS
    tokens = (
        # Identificadores y literales
        "IDENTIFIER",
        "INTEGER",
        "FLOAT_NUMBER",
        "STRING",
        # Operadores relacionales
        "EQ",
        "NE",
        "GT",
        "LT",
        "GE",
        "LE",
        # Operadores aritméticos
        "PLUS",
        "MINUS",
        "TIMES",
        "DIV",
        "MOD",
        "INC",
        "DEC",
        # Operadores de asignación compuesta
        "PLUSEQ",
        "MINUSEQ",
        "TIMESEQ",
        "DIVEQ",
        # Delimitadores
        "COLON",
        "COMMA",
        "SEMICOLON",
        "DOT",
        # Agrupadores
        "LBRACKET",
        "RBRACKET",
        "LPAREN",
        "RPAREN",
        "LBRACE",
        "RBRACE",
        # Asignación
        "ASSIGN",
        # Keywords
        "LET",
        "IF",
        "ELSE",
        "WHILE",
        "FOR",
        "RETURN",
        "STRUCT",
        # Tipos
        "INT",
        "FLOAT",
        "BOOL",
        # Lógicos
        "AND",
        "OR",
        "NOT",
        # Booleanos
        "TRUE",
        "FALSE",
        # Funciones especiales
        "PUSH",
        "GET",
        # Control
        "NEWLINE",
    )

    # PALABRAS RESERVADAS
    reserved = {
        # Control
        "let": "LET",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "for": "FOR",
        "return": "RETURN",
        # Estructuras
        "struct": "STRUCT",
        # Tipos
        "int": "INT",
        "float": "FLOAT",
        "bool": "BOOL",
        # Lógicos
        "and": "AND",
        "or": "OR",
        "not": "NOT",
        # Booleanos
        "true": "TRUE",
        "false": "FALSE",
        # Funciones
        "push": "PUSH",
        "get": "GET",
    }

    # Ignorar espacios y tabs
    t_ignore = " \t"

    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.lexer = lex.lex(module=self)

    # CLASIFICACIÓN
    def classify_token(self, tok):
        if tok.type in [
            "PLUS", "MINUS", "TIMES", "DIV",
            "MOD", "INC", "DEC"
        ]:
            return "ARITHMETIC_OP"
        elif tok.type in [
            "EQ", "NE", "GT", "LT", "GE", "LE"
        ]:
            return "RELATIONAL_OP"
        elif tok.type in [
            "AND", "OR", "NOT"
        ]:
            return "LOGICAL_OP"
        elif tok.type in [
            "IF", "ELSE", "WHILE",
            "FOR", "RETURN"
        ]:
            return "CONTROL"
        elif tok.type in [
            "INT", "FLOAT", "BOOL"
        ]:
            return "TYPE"
        elif tok.type == "STRUCT":
            return "STRUCTURE"
        elif tok.type in [
            "TRUE", "FALSE"
        ]:
            return "BOOLEAN"
        elif tok.type in [
            "INTEGER", "FLOAT_NUMBER"
        ]:
            return "NUMERIC_LITERAL"
        elif tok.type == "STRING":
            return "STRING_LITERAL"
        elif tok.type == "IDENTIFIER":
            return "IDENTIFIER"
        elif tok.type in [
            "LPAREN", "RPAREN",
            "LBRACE", "RBRACE",
            "LBRACKET", "RBRACKET"
        ]:
            return "PARENTHESIS"
        elif tok.type in [
            "COMMA", "COLON",
            "SEMICOLON", "DOT"
        ]:
            return "PUNCTUATION"
        elif tok.type in [
            "ASSIGN",
            "PLUSEQ",
            "MINUSEQ",
            "TIMESEQ",
            "DIVEQ"
        ]:
            return "ASSIGNMENT_OP"
        else:
            return "SYMBOL"

    def find_column(self, token):
        line_start = self.lexer.lexdata.rfind(
            '\n', 0, token.lexpos
        ) + 1
        return (token.lexpos - line_start) + 1
    # -------------------------
    # Tokens (t_ functions)
    # -------------------------
    def t_IDENTIFIER(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.reserved.get(
            t.value,
            "IDENTIFIER"
        )

        if t.type == "IDENTIFIER":
            if t.value not in self.symbol_table:

                self.symbol_table[t.value] = {
                    "type": None,
                    "value": None,
                    "occurrences": []
                }

            self.symbol_table[t.value][
                "occurrences"
            ].append(t.lexer.lineno)
        return t

    def t_FLOAT_NUMBER(self, t):
        r"\d+\.\d+"
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'(\"([^\\\n]|(\\.))*?\")|(\'([^\\\n]|(\\.))*?\')'
        return t

    def t_EQ(self, t): r"=="; return t
    def t_NE(self, t): r"!="; return t
    def t_GE(self, t): r">="; return t
    def t_LE(self, t): r"<="; return t
    def t_GT(self, t): r">"; return t
    def t_LT(self, t): r"<"; return t
    def t_PLUSEQ(self, t): r"\+="; return t
    def t_MINUSEQ(self, t): r"-="; return t
    def t_TIMESEQ(self, t): r"\*="; return t
    def t_DIVEQ(self, t): r"/="; return t
    def t_INC(self, t): r"\+\+"; return t
    def t_DEC(self, t): r"--"; return t
    def t_PLUS(self, t): r"\+"; return t
    def t_MINUS(self, t): r"-"; return t
    def t_TIMES(self, t): r"\*"; return t
    def t_DIV(self, t): r"/"; return t
    def t_MOD(self, t): r"%"; return t
    def t_COLON(self, t): r":"; return t
    def t_COMMA(self, t): r","; return t
    def t_SEMICOLON(self, t): r";"; return t
    def t_DOT(self, t): r"\."; return t
    def t_LBRACKET(self, t): r"\["; return t
    def t_RBRACKET(self, t): r"\]"; return t
    def t_LPAREN(self, t): r"\("; return t
    def t_RPAREN(self, t): r"\)"; return t
    def t_LBRACE(self, t): r"\{"; return t
    def t_RBRACE(self, t): r"\}"; return t
    def t_ASSIGN(self, t): r"="; return t

    def t_NEWLINE(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)
        return t

    def t_COMMENT(self, t):
        r"\#.*"
        pass

    def t_MULTILINE_COMMENT(self, t):
        r"/\*([^*]|\*+[^*/])*\*+/"
        t.lexer.lineno += t.value.count("\n")
        pass

    # ERRORES
    def t_error(self, t):
        error = {
            "line": t.lineno,
            "column": self.find_column(t),
            "character": t.value[0],
            "message": f"Illegal character '{t.value[0]}'"
        }

        self.errors.append(error)

        print(
            f"[LEX ERROR] "
            f"Line {error['line']} | "
            f"Column {error['column']} | "
            f"{error['message']}"
        )

        t.lexer.skip(1)

    # -------------------------
    # API para pipeline / GUI
    # -------------------------
    def analyze(self, data):
        self.symbol_table = {}
        self.errors = []

        self.lexer.input(data)

        tokens_list = []

        for tok in self.lexer:

            tokens_list.append({
                "type": tok.type,
                "value": tok.value,
                "line": tok.lineno,
                "column": self.find_column(tok),
                "category": self.classify_token(tok)
            })

        return tokens_list,self.symbol_table

def main():
    import sys
    lexer = Lexer()
    if len(sys.argv) < 2:
        print("Uso: python test_lexer.py <archivo>")
        return
    path = sys.argv[1]
    try:
        with open(path, "r") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"No se encontró el archivo: {path}")
        return

    tokens, table = lexer.analyze(code)
    print("\nTOKENS:\n")
    for t in tokens:
        print(f"{t['line']:>2} | {t['type']:<12} | {t['value']}")

    print("\nSYMBOL TABLE:\n")
    print(table)

if __name__ == "__main__":
    main()
