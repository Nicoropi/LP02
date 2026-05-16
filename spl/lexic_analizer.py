import ply.lex as lex

class Lexer:
    
    # 👇 tokens y reserved se quedan como atributos de clase
    tokens = (
        "IDENTIFIER","NUMBER","STRING","EQ","NE","GT","LT","GE","LE",
        "PLUS","MINUS","TIMES","DIV","INC","DEC",
        "COLON","COMMA","LBRACKET","RBRACKET","LPAREN","RPAREN",
        "NEWLINE","ASSIGN",
        "LET","IF","ELSE","WHILE",
        "AND","OR","NOT",
        "TRUE","FALSE",
        "PUSH","GET",
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

    def __init__(self):
        self.symbol_table = {}
        self.lexer = lex.lex(module=self)

    # -------------------------
    # Clasificación
    # -------------------------
    def classify_token(self, tok):
        if tok.type in ["PLUS", "MINUS", "TIMES", "DIV", "INC", "DEC"]:
            return "ARITHMETIC_OP"
        elif tok.type in ["EQ", "NE", "GT", "LT", "GE", "LE"]:
            return "RELATIONAL_OP"
        elif tok.type in ["AND", "OR", "NOT"]:
            return "LOGICAL_OP"
        elif tok.type in ["LET", "IF", "ELSE", "WHILE"]:
            return "CONTROL"
        elif tok.type in ["TRUE", "FALSE"]:
            return "BOOLEAN"
        elif tok.type == "NUMBER":
            return "LITERAL_NUMBER"
        elif tok.type == "STRING":
            return "LITERAL_STRING"
        elif tok.type == "IDENTIFIER":
            return "IDENTIFIER"
        else:
            return "SYMBOL"

    # -------------------------
    # Tokens (t_ functions)
    # -------------------------
    def t_IDENTIFIER(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.reserved.get(t.value, "IDENTIFIER")

        if t.type == "IDENTIFIER":
            if t.value not in self.symbol_table:
                self.symbol_table[t.value] = {
                    "type": None,
                    "value": None,
                    "occurrences": []
                }

            self.symbol_table[t.value]["occurrences"].append(t.lexer.lineno)

        return t

    def t_NUMBER(self, t):
        r"(\d+\.\d+|\d+)"
        t.value = float(t.value) if "." in t.value else int(t.value)
        return t

    def t_STRING(self, t):
        r"\"[^\"]*\"|'[^']*'"
        return t

    def t_EQ(self, t): r"=="; return t
    def t_NE(self, t): r"!="; return t
    def t_GE(self, t): r">="; return t
    def t_LE(self, t): r"<="; return t
    def t_GT(self, t): r">"; return t
    def t_LT(self, t): r"<"; return t
    def t_INC(self, t): r"\+\+"; return t
    def t_DEC(self, t): r"--"; return t
    def t_PLUS(self, t): r"\+"; return t
    def t_MINUS(self, t): r"-"; return t
    def t_TIMES(self, t): r"\*"; return t
    def t_DIV(self, t): r"/"; return t
    def t_COLON(self, t): r":"; return t
    def t_COMMA(self, t): r","; return t
    def t_LBRACKET(self, t): r"\["; return t
    def t_RBRACKET(self, t): r"\]"; return t
    def t_LPAREN(self, t): r"\("; return t
    def t_RPAREN(self, t): r"\)"; return t
    def t_ASSIGN(self, t): r"="; return t

    def t_NEWLINE(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)
        return t

    def t_comment(self, t):
        r"\#.*"
        pass

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
        t.lexer.skip(1)

    # -------------------------
    # API para pipeline / GUI
    # -------------------------
    def analyze(self, data):
        self.symbol_table = {}
        self.lexer.input(data)

        tokens_list = []

        for tok in self.lexer:
            tokens_list.append({
                "type": tok.type,
                "value": tok.value,
                "line": tok.lineno,
                "category": self.classify_token(tok)
            })

        return tokens_list, self.symbol_table
    
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

    for t in tokens:
        print(f"{t['line']:>2} | {t['type']:<12} | {t['value']}")

    print("\nSymbol table:")
    print(table)

if __name__ == "__main__":
    main()