import ply.yacc as yacc
from .lexic_analizer import Lexer

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # Stack of scopes
        self.structs = {}   # Map of struct definitions
        self.offset_stack = [0] # Offset tracking per scope level

    def enter_scope(self):
        self.scopes.append({})
        self.offset_stack.append(self.offset_stack[-1])

    def exit_scope(self):
        self.scopes.pop()
        self.offset_stack.pop()

    def declare(self, name, var_type, size=1):
        if name in self.scopes[-1]:
            raise Exception(f"Error: {name} already declared in this scope.")
        
        offset = self.offset_stack[-1]
        self.scopes[-1][name] = {'type': var_type, 'offset': offset, 'size': size}
        self.offset_stack[-1] += size
        return offset

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Error: Undefined variable {name}")

    def define_struct(self, name, members):
        # members: list of (type, member_name, size)
        struct_data = {}
        total_size = 0
        for m_type, m_name, m_size in members:
            struct_data[m_name] = {'type': m_type, 'offset': total_size, 'size': m_size}
            total_size += m_size
        self.structs[name] = {'members': struct_data, 'size': total_size}

class CodeGenerator:
    def __init__(self):
        self.st = SymbolTable()
        self.text = []
        self.functions = []
        self.data = []
        self.label_idx = 0
        self.emit("MOV", "BP", "SP")

    def new_label(self, prefix="L"):
        self.label_idx += 1
        return f"{prefix}_{self.label_idx}"

    def emit(self, instr, *params, section = None):
        if section is None:
            self.text.append(f"{instr} " + ", ".join(map(str, params)))
        else:
            section.append(f"{instr} " + ", ".join(map(str, params)))
    def _discover_structs(self, node):
        """
        Pasada preliminar: Escanea el AST buscando definiciones de estructuras 
        para registrarlas en la SymbolTable ANTES de generar código.
        """
        if node is None or not isinstance(node, tuple):
            return

        tag = node[0]

        # Agregamos FUNC_DEF para que busque structs dentro del cuerpo de las funciones
        if tag in ('PROGRAM', 'BLOCK'):
            for child in node[1]:
                self._discover_structs(child)
        
        elif tag == 'FUNC_DEF':
            # node es ('FUNC_DEF', tipo, nombre, parametros, bloque_cuerpo)
            # El bloque de código de la función está en node[4]
            self._discover_structs(node[4])

        elif tag == 'STRUCT_DEF':
            struct_name = node[1]
            decl_list = node[2]
            members = []
            
            for decl in decl_list:
                if decl[0] in ('DECL', 'DECL_ASSIGN'):
                    m_type = decl[1]
                    m_name = decl[2]
                    m_size = 1
                    members.append((m_type, m_name, m_size))
                elif decl[0] == 'DECL_ARRAY':
                    m_type = decl[1]
                    m_name = decl[2]
                    m_size = int(decl[3])
                    members.append((m_type, m_name, m_size))
            
            self.st.define_struct(struct_name, members)
            
    def generate(self, ast):
        self._discover_structs(ast)
        self.visit(ast)
        return "data:\n" + "\n".join(self.data) + "\ntext:\n" + "\n".join(self.text) + "\nHLT\n" + "\n".join(self.functions)

    def visit(self, node, in_func: bool = False):
        if node is None: return
        
        section = self.functions if in_func else None
        
        if not isinstance(node, tuple):
            # 1. Manejo de literales numéricos
            if isinstance(node, (int, float)): 
                self.emit("LDINT", "R5", node, section=section)
                return node
                
            # 2. Manejo de palabras clave booleanas literales
            if isinstance(node, str) and node in ("true", "false"):
                val = 1 if node == "true" else 0
                self.emit("LDINT", "R5", val, section=section)
                return node
                
            # 3. Manejo de variables reales (Cualquier otro string)
            if isinstance(node, str): 
                var = self.st.lookup(node)
                self.emit("LDINT", "R5", var['offset'], section=section)
                self.emit("ADD", "R5", "BP", "R5", section=section)
                self.emit("LOADMEM", "R5", "R5", section=section)
                return node
                
            return node
        
        tag = node[0]
        # print(node)

        if tag == 'PROGRAM':
            for child in node[1]: self.visit(child, in_func)

        elif tag == 'BLOCK':
            self.st.enter_scope()
            for stmt in node[1]: self.visit(stmt, in_func)
            self.st.exit_scope()
            
        elif tag == 'STRUCT_DEF':
            pass
        
        elif tag == 'DECL':
            self.st.declare(node[2], node[1], in_func)
            self.emit("INC", "SP") # Reserve stack space

        elif tag == 'DECL_ARRAY':
            size = int(node[3])
            self.st.declare(node[2], node[1], size=size)
            for _ in range(size): self.emit("INC", "SP", section=section)
        
        elif tag == 'ASSIGN':
            target = node[1]  # Puede ser un str ('n1') o una tupla ('MEMBER_ACCESS', ...)
            val = self.visit(node[2], in_func)  # Evalúa la expresión; el resultado queda en R5
            
            # CASO A: Asignación a un miembro de un Struct (e.g., n1.id = 5)
            if isinstance(target, tuple) and target[0] == 'MEMBER_ACCESS':
                base = target[1]    # e.g., 'n1' o 'this'
                member = target[2]  # e.g., 'id'
                
                # 1. Buscar la información de la variable base en la tabla de símbolos
                var_info = self.st.lookup(base)
                struct_type = var_info['type']
                
                # 2. Obtener el offset base de la variable en el Stack (BP + offset)
                self.emit("LDINT", "R1", var_info['offset'], section=section)
                self.emit("ADD", "R2", "BP", "R1", section=section)
                
                # 3. Cargar la dirección física real a la que apunta (puntero del Heap)
                self.emit("LOADMEM", "R3", "R2", section=section) # R3 = dirección base en el Heap
                
                # 4. Calcular el offset interno del miembro dentro del struct
                if struct_type not in self.st.structs:
                    raise Exception(f"Error semántico: Tipo de estructura '{struct_type}' no reconocida.")
                
                member_offset = self.st.structs[struct_type]['members'][member]['offset']
                
                # 5. Dirección final en el Heap = Base de la estructura + offset del miembro
                self.emit("LDINT", "R1", member_offset, section=section)
                self.emit("ADD", "R2", "R3", "R1", section=section) # R2 = dirección de memoria física exacta
                
                # 6. Guardar el valor (que está en R5) en esa dirección física del Heap
                self.emit("STOR", "R5", "R2", section=section)

            # CASO B: Asignación normal a una variable local/global (e.g., x = 10)
            else:
                var_name = target
                var_info = self.st.lookup(var_name)
                
                # Encontrar dirección en el Stack: base_ptr + offset
                self.emit("LDINT", "R1", var_info['offset'], section=section)
                self.emit("ADD", "R2", "BP", "R1", section=section) # R2 = dirección en Stack
                self.emit("STOR", "R5", "R2", section=section)      # Guarda el valor de R5 en el Stack

        elif tag == 'IF':
            label_end = self.new_label("end_if")
            self.visit(node[1], in_func)
            self.emit("JMPZ", label_end, section=section)
            self.visit(node[2], in_func)
            # Agrega la etiqueta con punto limpia (ej: .end_if_1)
            (section if in_func else self.text).append(f"{label_end}")

        elif tag == 'WHILE':
            label_start = self.new_label("while_start")
            label_end = self.new_label("while_end")
            # Palabras solas
            (section if in_func else self.text).append(f"{label_start}")
            print(node[1])
            self.visit(node[1], in_func)
            self.emit("JMPZ", label_end, section=section)
            self.visit(node[2], in_func)
            self.emit("JMP", label_start, section=section)
            (section if in_func else self.text).append(f"{label_end}")
            
        elif tag == 'FOR':
            l_start, l_end = self.new_label("for_start"), self.new_label("for_end")
            self.st.enter_scope()
            self.visit(node[1], in_func) # Init
            (section if in_func else self.text).append("{" + l_start + "}")
            self.visit(node[2], in_func) # Condition (R5 = result)
            self.emit("COMP", "R5", 0, section=section) # Assumes 0 is false
            self.emit("JMPZ", l_end, section=section)
            self.visit(node[4], in_func) # Body
            self.visit(node[3], in_func) # Update
            self.emit("JMP", l_start, section=section)
            (section if in_func else self.text).append("{" + l_end + "}")
            self.st.exit_scope()

        elif tag == 'FUNC_DEF':
            section = self.functions
            in_func = True
            # Le ponemos el punto adelante: .main
            self.functions.append(f".{node[2]}")
            self.st.enter_scope()
            self.emit("PUSH", "BP", section=section)
            self.emit("MOV", "BP", "SP", section=section)
            for type, name in node[3]:
                self.st.declare(name, type)
            self.visit(node[4], in_func)
            self.st.exit_scope()
            self.emit("POP", "BP", section=section)
            self.emit("POP", "PC", section=section)
            section = None
            in_func = False

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
            # 1. Push arguments
            for arg in reversed(node[2]):
                self.visit(arg, in_func)
                self.emit("PUSH", "R5", section=section)
            # 2. Call (jump)
            self.emit("PUSH", "PC", section=section) # Save return address
            self.emit("JMP", node[1], section=section)

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
            self.visit(node[1], in_func)
            self.emit("PUSH", "R5", section=section)
            self.visit(node[2], in_func)
            self.emit("POP", "R1", section=section)
            self.emit("AND", "R5", "R1", "R5", section=section)
            
        elif tag in ('+', '-', '*', '/'):
            # Arithmetic: Evaluate left, then right, then operate
            # This is a template for a recursive register-based generator
            self.visit(node[1], in_func)
            self.emit("PUSH", "R5", section=section)
            self.visit(node[2], in_func)
            self.emit("POP", "R1", section=section)
            op = {'+':'ADD', '-':'SUB', '*':'MUL', '/':'DIV'}[tag]
            self.emit(op, "R5", "R1", "R5", section=section)
        
        elif tag == 'NEW_OBJECT':
            struct_name = node[1]
            if struct_name not in self.st.structs:
                raise Exception(f"Error semántico: Estructura '{struct_name}' no definida.") 
            size = self.st.structs[struct_name]['size']
            self.emit("LDINT", "R1", size, section=section)
            
            # Cambiamos "SYS_ALLOC" por la palabra mágica que intercepta tu cpu.py
            self.emit("0xEEEEEEEEEEEEEEEE", section=section) 
            return "VALUE_IN_R5"
        
        if tag == 'DECL_ASSIGN':
            offset = self.st.declare(node[2], node[1])
            self.visit(node[3], in_func) # Evaluate Expr into R5
            self.emit("LDINT", "R1", offset, section=section)
            self.emit("ADD", "R2", "BP", "R1", section=section)
            self.emit("STOR", "R5", "R2", section=section)
            self.emit("INC", "SP", section=section)

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
   
    def new_label(self, prefix="L"):
        self.label_idx += 1
        # Agregamos un punto adelante para denotar etiqueta de salto
        return f".{prefix}_{self.label_idx}"

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

    def p_arit_factor_new(self, p):
        '''AritFactor : IDENTIFIER NEW'''
        p[0] = ('NEW_OBJECT', p[1])

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
