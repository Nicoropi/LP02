import ply.yacc as yacc
from lexic_analizer import Lexer

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.structs = {}
        
        self.offset_stack = [0]

    def enter_scope(self):
        self.scopes.append({})
        self.offset_stack.append(self.offset_stack[-1])

    def reset_function_offsets(self):
        self.offset_stack[-1] = 0

    def exit_scope(self):
        self.scopes.pop()
        self.offset_stack.pop()

    def declare(self, name, var_type, size=1, is_global=False):
        if name in self.scopes[-1]:
            raise Exception(f"Error: {name} already declared")

        if is_global:
            offset = None

        else:
            offset = self.offset_stack[-1]
            self.offset_stack[-1] -= size

        self.scopes[-1][name] = {
            'type': var_type,
            'offset': offset,
            'size': size,
            'global': is_global
        }

        return offset

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise Exception(f"Undefined variable {name}")

    def define_struct(self, name, members):
        struct_data = {}
        total_size = 0

        for m_type, m_name, m_size in members:
            struct_data[m_name] = {
                'type': m_type,
                'offset': total_size,
                'size': m_size
            }
            total_size += m_size

        self.structs[name] = {
            'members': struct_data,
            'size': total_size
        }

class CodeGenerator:
    def __init__(self):
        self.st = SymbolTable()

        self.text = []
        self.functions = []
        self.data = []

        self.label_idx = 0
        self.current_function = None
        self.in_function = False

        self.emit("MOV", "BP", "SP")

    def new_label(self, prefix="L"):
        self.label_idx += 1
        return f"{prefix}_{self.label_idx}"

    def current_section(self):
        return self.functions if self.in_function else self.text

    def place_label(self, label):
        self.current_section().append(f"{{{label}}}")

    def load_variable(self, name, target="R5"):
        info = self.st.lookup(name)

        if info['global']:
            self.emit("LDINT", "R1", f"global_{name}")
            self.emit("LOADMEM", target, "R1")
        else:
            self.emit("LDINT", "R1", info['offset'])
            self.emit("ADD", "R1", "BP", "R1")
            self.emit("LOADMEM", target, "R1")

    def store_variable(self, name, source="R5"):
        info = self.st.lookup(name)

        if info['global']:
            self.emit("LDINT", "R1", f"global_{name}")
            self.emit("STOR", source, "R1")
        else:
            self.emit("LDINT", "R1", info['offset'])
            self.emit("ADD", "R1", "BP", "R1")
            self.emit("STOR", source, "R1")

    def emit_condition_jump_false(self, condition, label):
        self.visit(condition)
        self.emit("LDINT", "RA", "0")
        self.emit("COMP", "R5", "RA")
        self.emit("JMPZ", label)

    def emit(self, instr, *params, section=None):
        if section is None:
            section = self.current_section()

        if len(params) == 0:
            section.append(instr)
        else:
            section.append(f"{instr} " + ", ".join(map(str, params)))

    def generate(self, ast):
        self.visit(ast)

        return (
            "data:\n"
            + "\n".join(self.data)
            + "\ntext:\n"
            + "\n".join(self.text)
            + "\nHLT\n"
            + "\n".join(self.functions)
        )

    def visit(self, node, in_func: bool = False):
        if node is None: return
        
        section = self.functions if in_func else None
        
        if not isinstance(node, tuple):
            if isinstance(node, int):
                self.emit("LDINT", "R5", node)
                return

            if isinstance(node, float):
                self.emit("LOADFLOAT", "R5", node)
                return

            if isinstance(node, str):
                self.load_variable(node)
                return
        
        tag = node[0]
        # print(node)

        if tag == 'PROGRAM':
            for child in node[1]: self.visit(child, in_func)

        elif tag == 'BLOCK':
            self.st.enter_scope()
            for stmt in node[1]: self.visit(stmt, in_func)
            self.st.exit_scope()

        elif tag == 'DECL':
            is_global = not self.in_function

            if is_global:
                self.st.declare(node[2], node[1], is_global=True)
                self.data.append(f"{{global_{node[2]}}}")
                self.data.append("0")
            else:
                self.st.declare(node[2], node[1])
                self.emit("DEC", "SP")

        elif tag == 'DECL_ASSIGN':
            is_global = not self.in_function

            if is_global:
                self.st.declare(node[2], node[1], is_global=True)

                if isinstance(node[3], int):
                    value = node[3]
                else:
                    value = 0

                self.data.append(f"{{global_{node[2]}}}")
                self.data.append(str(value))

            else:
                self.st.declare(node[2], node[1])
                self.emit("DEC", "SP")
                self.visit(node[3])
                self.store_variable(node[2])
        
        elif tag == 'DECL_ARRAY':
            size = int(node[3])
            self.st.declare(node[2], node[1], size=size)
            for _ in range(size): self.emit("DEC", "SP", section=section)
        
        elif tag == 'ASSIGN':
            self.visit(node[2])
            self.store_variable(node[1])

        elif tag == 'IF':
            l_end = self.new_label("if_end")

            self.emit_condition_jump_false(node[1], l_end)

            self.visit(node[2])

            self.place_label(l_end)

        elif tag == 'IF_ELSE':
            l_else = self.new_label("if_else")
            l_end = self.new_label("if_end")

            self.emit_condition_jump_false(node[1], l_else)

            self.visit(node[2])
            self.emit("JMP", l_end)

            self.place_label(l_else)
            self.visit(node[3])

            self.place_label(l_end)

        elif tag == 'WHILE':
            l_start = self.new_label("while_start")
            l_end = self.new_label("while_end")

            self.place_label(l_start)

            self.emit_condition_jump_false(node[1], l_end)

            self.visit(node[2])

            self.emit("JMP", l_start)

            self.place_label(l_end)

        elif tag == 'FOR':
            l_start = self.new_label("for_start")
            l_end = self.new_label("for_end")

            self.st.enter_scope()

            self.visit(node[1])

            self.place_label(l_start)

            self.emit_condition_jump_false(node[2], l_end)

            self.visit(node[4])
            self.visit(node[3])

            self.emit("JMP", l_start)

            self.place_label(l_end)

            self.st.exit_scope()
            
        elif tag == 'RETURN':
            self.visit(node[1])
            self.emit("MOV", "RA", "R5")

            self.emit("MOV", "SP", "BP")
            self.emit("POP", "BP")
            self.emit("POP", "PC")
            
        elif tag == 'FUNC_DEF':
            prev = self.in_function
            self.in_function = True
            self.current_function = node[2]

            self.place_label(node[2])

            self.st.enter_scope()
            self.st.reset_function_offsets()

            self.emit("PUSH", "BP")
            self.emit("MOV", "BP", "SP")

            params = node[3]

            reg_params = ["R1", "R2", "R3", "R4", "R5"]

            stack_params_off = 2
            
            for idx, (ptype, pname) in enumerate(params):

                if idx < 5: #parametros en registro
                    offset = self.st.declare(pname, ptype)
                    self.emit("DEC", "SP")
                    self.emit("LDINT", "RB", offset)
                    self.emit("ADD", "RB", "BP", "RB")
                    self.emit("STOR", reg_params[idx], "RB")
                
                else: # parametros en stack
                    #manualmente adicionar a la tabla por complejidad
                    self.st.scopes[-1][pname] = {
                        'type': ptype,
                        'offset': stack_param_offset,
                        'size': 1,
                        'global': False,
                        'param': True
                    }

                    stack_param_offset += 1

            self.visit(node[4])

            self.emit("MOV", "SP", "BP")
            self.emit("POP", "BP")
            self.emit("POP", "PC")

            self.st.exit_scope()

            self.current_function = None
            self.in_function = prev

        elif tag == 'METHOD_DEF':
            # Method: struct_name.method_name
            method_label = f"{node[2]}_{node[4]}"
            self.text.append("{" + method_label + "}")
            self.st.enter_scope()
            # Param 0 is the hidden 'this' pointer (hidden address)
            self.st.declare("this", node[2]) 
            self.visit(node[8], in_func)
            self.st.exit_scope()
            self.emit("POP", "PC", section=section)

        elif tag == 'CALL_FUNC':
            args = node[2]
            reg_params = ["R1", "R2", "R3", "R4", "R5"]

            stack_args = args[5:]

            for arg in reversed(stack_args):
                self.visit(arg)
                self.emit("PUSH", "R5")

            if len(args) >= 5:
                self.visit(arg[5])
                self.emit("PUSH", "R5")

            N = len(args) if len(args) < 4 else 4
            for idx, arg in enumerate(reversed(args[:4]), 1):
                self.visit(arg)
                self.emit("MOV", reg_params[N-idx], "R5")
            
            if len(args) >= 5:
                self.emit("POP", "R5")

            ret_label = self.new_label("ret")

            self.emit("LOADINT", "RC", ret_label)
            self.emit("PUSH", "RC")

            self.emit("JMP", node[1])
            
            self.place_label(ret_label)
            self.emit("MOV", "R5", "RA")
            

        elif tag == 'CALL_METHOD':
            # hidden 'this' logic
            instance = node[1] # can be complex access
            # 1. Push args
            for arg in reversed(node[2]):
                self.visit(arg, in_func)
                self.emit("PUSH", "R5", section=section)
            # 2. Push address of instance as 'this'
            self.emit("LDINT", "R1", self.st.lookup(instance[1])['offset'], section=section)
            self.emit("ADD", "R5", "BP", "R1", section=section)
            self.emit("PUSH", "R5", section=section) # 'this' is now on top of args
            # 3. Call
            self.emit("PUSH", "PC", section=section)
            # Method label format: StructName_MethodName
            self.emit("JMP", f"{self.st.lookup(instance[1])['type']}_{instance[2]}", section=section)

        elif tag == 'AND':
            self.visit(node[1])
            self.emit("PUSH", "R5")

            self.visit(node[2])
            self.emit("POP", "R1")

            self.emit("AND", "R5", "R1", "R5")
        
        elif tag == 'OR':
            self.visit(node[1])
            self.emit("PUSH", "R5")

            self.visit(node[2])
            self.emit("POP", "R1")

            self.emit("OR", "R5", "R1", "R5")
        
        elif tag == 'NOT':
            self.visit(node[1])
            self.emit("NOT", "R5", "R5")
            
        elif tag in ('+', '-', '*', '/'):
            self.visit(node[1])
            self.emit("PUSH", "R5")

            self.visit(node[2])
            self.emit("POP", "R1")

            op = {
                '+': 'ADD',
                '-': 'SUB',
                '*': 'MUL',
                '/': 'DIV'
            }[tag]

            self.emit(op, "R5", "R1", "R5")

        elif tag in ('<', '>', '<=', '>=', '==', '!='):
            op = tag

            self.visit(node[1])
            self.emit("PUSH", "R5")

            self.visit(node[2])
            self.emit("POP", "R1")

            self.emit("COMP", "R1", "R5")

            l_true = self.new_label("rel_true")
            l_end = self.new_label("rel_end")

            if op == '<':
                self.emit("JMPN", l_true)

            elif op == '>':
                self.emit("JMPNN", l_true)
                self.emit("JMPZ", l_end)

            elif op == '==':
                self.emit("JMPZ", l_true)

            elif op == '!=':
                self.emit("JMPNZ", l_true)

            elif op == '<=':
                self.emit("JMPN", l_true)
                self.emit("JMPZ", l_true)

            elif op == '>=':
                self.emit("JMPNN", l_true)

            self.emit("LDINT", "R5", 0)
            self.emit("JMP", l_end)

            self.place_label(l_true)
            self.emit("LDINT", "R5", 1)

            self.place_label(l_end)

        elif tag == 'INC_VAR':
            self.load_variable(node[1])
            self.emit("INC", "R5")
            self.store_variable(node[1])

        elif tag == 'DEC_VAR':
            self.load_variable(node[1])
            self.emit("DEC", "R5")
            self.store_variable(node[1])

        elif tag == 'MEMBER_ACCESS':
            # this.x logic
            base = node[1] # e.g., 'this'
            member = node[2] # e.g., 'x'
            
            # Get the address stored in 'this'
            var_info = self.st.lookup(base)
            self.emit("LDINT", "R1", var_info['offset'], section=section)
            self.emit("ADD", "R2", "BP", "R1", section=section)
            self.emit("LOADMEM", "R3", "R2", section=section) # R3 now holds the base address of the struct
            
            # Get the offset of the member inside that struct
            struct_type = var_info['type']
            member_offset = self.st.structs[struct_type]['members'][member]['offset']
            
            self.emit("LDINT", "R1", member_offset, section=section)
            self.emit("ADD", "R2", "R3", "R1", section=section) # Final address = Base of struct + member offset
            self.emit("LOADMEM", "R5", "R2", section=section)   # Value into R5
            return ("ADDRESS_IN_R2", "VALUE_IN_R5")

class Parser:
    def __init__(self):
        self.lexer_instance = Lexer()
        self.tokens = self.lexer_instance.tokens
        self.parser = yacc.yacc(module=self)

    # Program & Blocks
    def p_programa(self, p):
        '''Programa : bloque_list'''
        p[0] = ('PROGRAM', p[1])

    def p_bloque_list(self, p):
        '''bloque_list : bloque_list Bloque
                       | empty'''
        p[0] = p[1] + [p[2]] if len(p) == 3 and p[2] else (p[1] if len(p) == 3 else [])

    def p_bloque(self, p):
        '''Bloque : sentencia_list'''
        p[0] = ('BLOCK', p[1])

    def p_sentencia_list(self, p):
        '''sentencia_list : sentencia_list Sentencia
                          | empty'''
        p[0] = p[1] + [p[2]] if len(p) == 3 and p[2] else (p[1] if len(p) == 3 else [])

    # Sentences
    def p_sentencia(self, p):
        '''Sentencia : Declaracion SEMICOLON
                     | Estructura
                     | Funcion
                     | Metodo
                     | Asignacion SEMICOLON
                     | LlamadoFun SEMICOLON
                     | LlamadoMet SEMICOLON
                     | While
                     | For
                     | If
                     | RETURN Expr SEMICOLON'''
        p[0] = p[1] if len(p) <= 3 else ('RETURN', p[2])

    def p_if(self, p):
        '''If : IF LPAREN Expr RPAREN LBRACE Bloque RBRACE ELSE LBRACE Bloque RBRACE
              | IF LPAREN Expr RPAREN LBRACE Bloque RBRACE'''
        if len(p) == 12: p[0] = ('IF_ELSE', p[3], p[6], p[10])
        else: p[0] = ('IF', p[3], p[6])

    def p_while(self, p):
        '''While : WHILE LPAREN BoolExpr RPAREN LBRACE Bloque RBRACE'''
        p[0] = ('WHILE', p[3], p[6])

    # --- FOR LOOP (NEW) ---
    def p_for(self, p):
        '''For : FOR LPAREN ForInit SEMICOLON Expr SEMICOLON ForUpdate RPAREN LBRACE Bloque RBRACE'''
        p[0] = ('FOR', p[3], p[5], p[7], p[10])

    def p_for_init(self, p):
        '''ForInit : Declaracion
                   | Asignacion'''
        p[0] = p[1]

    def p_for_update(self, p):
        '''ForUpdate : Asignacion
                     | Incremento
                     | Decremento'''
        p[0] = p[1]

    def p_incremento(self, p):
        '''Incremento : IDENTIFIER INC'''
        p[0] = ('INC_VAR', p[1])

    def p_decremento(self, p):
        '''Decremento : IDENTIFIER DEC'''
        p[0] = ('DEC_VAR', p[1])

    # --- BOOLEAN EXPRESSIONS (NEW) ---
    def p_bool_expr(self, p):
        '''BoolExpr : BoolExpr OR BoolTerm
                    | BoolTerm'''
        p[0] = ('OR', p[1], p[3]) if len(p) == 4 else p[1]

    def p_bool_term(self, p):
        '''BoolTerm : BoolTerm AND BoolFactor
                    | BoolFactor'''
        p[0] = ('AND', p[1], p[3]) if len(p) == 4 else p[1]

    def p_bool_factor(self, p):
        '''BoolFactor : NOT BoolFactor
                      | LPAREN BoolExpr RPAREN
                      | TRUE
                      | FALSE
                      | Relacion
                      | LlamadoFun
                      | LlamadoMet
                      | AccesoStruc'''
        if len(p) == 3: p[0] = ('NOT', p[2])
        elif len(p) == 4: p[0] = p[2]
        else: p[0] = p[1]

    # --- CALLS (NEW) ---
    def p_llamado_fun(self, p):
        '''LlamadoFun : IDENTIFIER LPAREN exprs_opt RPAREN'''
        p[0] = ('CALL_FUNC', p[1], p[3])

    def p_llamado_met(self, p):
        '''LlamadoMet : AccesoStruc LPAREN exprs_opt RPAREN'''
        p[0] = ('CALL_METHOD', p[1], p[3])

    def p_exprs_opt(self, p):
        '''exprs_opt : Exprs
                     | empty'''
        p[0] = p[1] if p[1] else []

    def p_exprs(self, p):
        '''Exprs : Expr
                 | Exprs COMMA Expr'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    # Structs & Methods
    def p_estructura(self, p):
        '''Estructura : STRUCT IDENTIFIER LBRACE decl_plus RBRACE'''
        p[0] = ('STRUCT_DEF', p[2], p[4])

    def p_decl_plus(self, p):
        '''decl_plus : Declaracion SEMICOLON
                     | decl_plus Declaracion SEMICOLON'''
        p[0] = [p[1]] if len(p) == 3 else p[1] + [p[2]]

    def p_metodo(self, p):
        '''Metodo : Tipo IDENTIFIER DOT IDENTIFIER LPAREN parametros_opt RPAREN LBRACE Bloque RBRACE'''
        p[0] = ('METHOD_DEF', p[1], p[2], p[4], p[6], p[9])

    # Declarations & Arrays (Added Array Support)
    def p_declaracion(self, p):
        '''Declaracion : Tipo IDENTIFIER ASSIGN Expr
                       | Tipo IDENTIFIER
                       | Tipo IDENTIFIER LBRACKET INTEGER RBRACKET'''
        if len(p) == 5: p[0] = ('DECL_ASSIGN', p[1], p[2], p[4])
        elif len(p) == 3: p[0] = ('DECL', p[1], p[2])
        else: p[0] = ('DECL_ARRAY', p[1], p[2], p[4])

    def p_asignacion(self, p):
        '''Asignacion : IDENTIFIER ASSIGN Expr
                      | AccesoStruc ASSIGN Expr
                      | IDENTIFIER LBRACKET Expr RBRACKET ASSIGN Expr'''
        if len(p) == 4: p[0] = ('ASSIGN', p[1], p[3])
        else: p[0] = ('ASSIGN_ARRAY', p[1], p[3], p[6])

    # Expressions
    def p_expr(self, p):
        '''Expr : AritExpr
                | BoolExpr'''
        p[0] = p[1]

    def p_arit_expr(self, p):
        '''AritExpr : AritExpr PLUS AritTerm
                    | AritExpr MINUS AritTerm
                    | AritTerm'''
        p[0] = (p[2], p[1], p[3]) if len(p) == 4 else p[1]

    def p_arit_term(self, p):
        '''AritTerm : AritTerm TIMES AritFactor
                    | AritTerm DIV AritFactor
                    | AritFactor'''
        p[0] = (p[2], p[1], p[3]) if len(p) == 4 else p[1]

    def p_arit_factor(self, p):
        '''AritFactor : LPAREN Expr RPAREN
                      | INTEGER
                      | FLOAT_NUMBER
                      | IDENTIFIER
                      | AccesoStruc
                      | IDENTIFIER LBRACKET Expr RBRACKET'''
        if len(p) == 4: p[0] = p[2]
        elif len(p) == 5: p[0] = ('ARRAY_ACCESS', p[1], p[3])
        else: p[0] = p[1]

    def p_relacion(self, p):
        '''Relacion : AritExpr RelOp AritExpr'''
        p[0] = (p[2], p[1], p[3])

    def p_rel_op(self, p):
        '''RelOp : LT
                 | GT
                 | LE
                 | GE
                 | EQ
                 | NE'''
        p[0] = p[1]

    def p_acceso_struc(self, p):
        '''AccesoStruc : IDENTIFIER DOT IDENTIFIER
                       | AccesoStruc DOT IDENTIFIER'''
        p[0] = ('MEMBER_ACCESS', p[1], p[3])

    def p_funcion(self, p):
        '''Funcion : Tipo IDENTIFIER LPAREN parametros_opt RPAREN LBRACE Bloque RBRACE'''
        p[0] = ('FUNC_DEF', p[1], p[2], p[4], p[7])

    def p_parametros_opt(self, p):
        '''parametros_opt : Parametros
                          | empty'''
        p[0] = p[1] if p[1] else []

    def p_Parametros(self, p):
        '''Parametros : Parametro
                      | Parametros COMMA Parametro'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_Parametro(self, p):
        '''Parametro : Tipo IDENTIFIER'''
        p[0] = (p[1], p[2])

    def p_tipo(self, p):
        '''Tipo : INT
                | FLOAT
                | BOOL
                | IDENTIFIER'''
        p[0] = p[1]

    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        print(f"Parser Error: Unexpected {p.type if p else 'EOF'}")

    def parse(self, code):
        return self.parser.parse(code)

def main():
    import sys
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

    p = Parser()
    ast = p.parse(code)
    gen = CodeGenerator()
    assembly = gen.generate(ast)
    print(assembly)

if __name__ == "__main__":
    main()