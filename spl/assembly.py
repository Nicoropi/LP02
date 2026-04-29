import sys
from ply import lex
from enum import Enum, auto
from struct import pack #para conversion a binario
from math import ceil

REGISTERS = {
    'PC': 0x1, 'SP': 0x2, 'BP': 0x3, 'IR': 0x4, 
    'RA': 0x5, 'RB': 0x6, 'RC': 0x7, 'RD': 0x8, 'RE': 0x9,
    'R1': 0xA, 'R2': 0xB, 'R3': 0xC, 'R4': 0xD, 'R5': 0xE,
}

class ParamType(Enum):
    _   = auto()    #sin parametros
    r   = auto()    #un registro
    rr  = auto()    #dos registros
    rrr = auto()    #tres registros
    i   = auto()    #un entero
    ri  = auto()    #un registro y un entero
    rf  = auto()    #un registro y un flotante
    
    @classmethod
    def len(cls, enumerated: int):
        if enumerated == cls._:
            return 0
        elif enumerated in [cls.r, cls.i]:
            return 1
        elif enumerated in [cls.rr, cls.ri, cls.rf]:
            return 2
        elif enumerated == cls.rrr:
            return 3
    
    @classmethod
    def correctParam(cls, enumerated: int, type: str, position: int) -> bool | tuple[bool,str]:
        ptypeMap = {
            cls._:   [],
            cls.r:   ["REG"],
            cls.rr:  ["REG", "REG"],
            cls.rrr: ["REG", "REG", "REG"],
            cls.i:   ["INT"],
            cls.ri:  ["REG", "INT"],
            cls.rf:  ["REG", "FLOAT"]
        }
        params = ptypeMap.get(enumerated, [])
        if len(params) <= position:
            return False
        if type == "ID": type = "INT"
        return params[position] == type, params[position]
        
class Builder:
    _readableModes: dict[str, str] = {
        "b":            ("0b{0:{1}b}", 1),
        "bin":          ("0b{0:{1}b}", 1),
        "binary":       ("0b{0:{1}b}", 1),
        "hex":          ("0x{0:{1}X}", 4),
        "hexadecimal":  ("0x{0:{1}X}", 4),
    }
    
    _jumps: set[str] = {
        "JMP",
        "JMPZ",
        "JMPNZ",
        "JMPN",
        "JMPNN",
        "JMPOVR",
        "JMPUND",
        "JMPNORZ",
        "JMPNANDZ"
    }
    
    def __init__(self, format: str = "b"):
        if format.lower() not in self._readableModes: raise ValueError(f"Error: formato \"{format}\" no reconocido")
        self._format = self._readableModes[format.lower()]
        
        self._sectionIsText: bool = True
        self._expect: None | str = None
        
        self._textOutput: list[str] = []
        self._dataOutput: list[str] = []
        
        self._textLabels: list[tuple[str, int]] = []
        self._dataLabels: list[tuple[str, int]] = []
        self._inst: str = None
        self._instBase: int = None
        self._expectedParams: ParamType = None
        self._paramsLen: list[int] = None
        self._params: list[int|float|str] = []
        self._labels: dict[str, str] = {}
        self._hasErrors = False
    
    def encodeInt(self, val: int, size: int | None = None) -> str:
        if size:
            ones = (1 << size) - 1
            if val < 0:
                val = ones ^ (val & ones) + 1 #complemento de 2
            else:
                val &= ones
        
        return self._format[0].format(val, f"0{ceil(size / self._format[1])}" if size is not None else "") 
    
    def encodeReplace(self, label: str, size: int) -> str:
        return "{" + label + ":" + self.encodeInt(size) + "}"
    
    def checkExpected(self, pos: str):
        if not self._expect:
            return
        if self._expect == ",":
            print(f"Error en {pos}: se espera el separador \",\" entre parametros")
            self._hasErrors = True
        elif self._expect == ":":
            print(f"Error en {pos}: se espera el separador \":\" despues de definir una seccion")
            self._hasErrors = True
        self._expect = None
    
    def instruction(self, inst: str, pos: str) -> None:
        if not self._sectionIsText:
            print(f"Error en {pos}: no se puede colocar instrucciones en la secion data")
            self._hasErrors = True
            return
        if self._inst != None:
            print(f"Error en {pos}: no se puede iniciar una instruccion dentro de otra")
            self._hasErrors = True
            return
        self._inst = inst
        self._expectedParams, self._instBase, self._paramsLen = INSTRUCTION[inst.upper()]
    
    def section(self, section: str, pos):
        if self._inst != None:
            print(f"Error en {pos}: no se termino la instruccion")
            self._hasErrors = True
            return
        
        self._expect = ":"
        
        self._sectionIsText = section.upper() == "TEXT"
    
    def literal(self, literal: str, pos: str ):
        if not self._expect or literal not in self._expect:
            self._expect = None
            print(f"Error en {pos}: literal \"{literal}\" inesperado")
            self._hasErrors = True
            return
        self._expect = None
    
    def parameter(self, type: str, value: int | float | str, pos: str) -> None:
        
        #si esta en la seccion data guardar dato directamente
        if not self._sectionIsText:
            self._expect = ","
            if type == "ID":
                value = self.encodeReplace(value)
            elif type == "FLOAT": #convertir floante a representacion binaria
                value = self.encodeInt(int.from_bytes(pack(">d", value)),64)
            else:
                value = self.encodeInt(value, 64)
            self._dataOutput.append(value)
            return
        
        if self._inst == None:
            print(f"Error en {pos}: se esperaba una instruccion")
            self._hasErrors = True
            return
        
        self._expect = ","
        
        expectedLen = ParamType.len(self._expectedParams)
        if len(self._params) + 1 > expectedLen:
            print(f"Error en {pos}: {expectedLen} argumentos esperados para instruccion {self._inst}")
            self._hasErrors = True
            return
        
        isCorrectType, correctType = ParamType.correctParam(
            self._expectedParams, type, len(self._params))
        if not isCorrectType:
            print(f"Error en {pos}: la instruccion \"{self._inst}\" esperaba un parametro tipo \"{correctType}\" no {type}")
            self._hasErrors = True
            return
        self._params.append(value)
    
    def labelDef(self, label: str, pos: str) -> None:
        if self._inst != None:
            print(f"Advertencia en {pos}: definicion de etiqueta dentro de instruccion")
        
        self._expect = ","
        
        if label in self._labels:
            print(f"Error en {pos}: etiqueta ya definida antes en {self._labels[label]}")
            self._hasErrors = True
            return
        L = label.upper()
        if L in INSTRUCTION or L in REGISTERS or L in ["TEXT", "DATA"]:
            print(f"Error en {pos}: no se permiten etiquetas con el nombre de palabras reservadas")
            self._hasErrors = True
            return
        
        self._labels[label] = pos
        if self._sectionIsText:
            self._textLabels.append((label, len(self._textOutput)))
        else:
            self._dataLabels.append((label, len(self._dataOutput)))
    
    def clearInstruction(self) -> None:
        self._inst = None
        self._instBase = None
        self._expectedParams = None
        self._paramsLen = None
        self._params = []
    
    def instructionEnd(self, pos: str):
        if self._expect == ",": self._expect = None
        
        if self._inst == None or not self._sectionIsText:
            return
        expectedLen = ParamType.len(self._expectedParams)
        if len(self._params) != expectedLen:
            print(f"Error en {pos}: {expectedLen} argumentos esperados para instruccion {self._inst}")
            self._hasErrors = True
            self.clearInstruction()
            return
        
        encoded: list[str] = []
        word = 0
        nParams = len(self._params)
        accOcupied = sum(self._paramsLen[:nParams-1:-1])
        accStored = 0
        for param, pLen in zip(self._params[::-1], self._paramsLen[nParams-1::-1]):
            if isinstance(param, str) or self._inst in self._jumps:
                if accOcupied > 0:
                    encoded.insert(0, self.encodeInt(word, accOcupied - accStored))
                encoded.insert(0, self.encodeReplace(param, pLen))
                word = 0
                accOcupied += pLen
                accStored = accOcupied
                continue
                    
            if isinstance(param, float):
                #convertir float a representacion binaria
                significant = int.from_bytes(pack(">d", param))
                #truncar float para guardar bits mas significativos
                significant >>= 64 - pLen
                param = significant
            
            word |= (param & self.len2mask(pLen)) << accOcupied - accStored
            accOcupied += pLen
        word |= self._instBase << accOcupied - accStored
        encoded.insert(0, self.encodeInt(word, 64 - accStored))
        self._textOutput.append("".join(encoded))
        
        self.clearInstruction()
    
    def len2mask(self, len: int):
        return (1 << len) - 1
    
    def encodeLabels(self, section: str, labels: list[tuple[str, int]]) -> str:
        if not labels: return ""
        ret = section + "Labels {\n"
        ret += "".join(f"{label}: {self.encodeInt(pos)}\n" for label, pos in labels)
        ret += "}\n"
        
        return ret
    
    def encodeSectionOutput(self, section: str, output: list[str]) -> str:
        if not output: return ""
        ret = section+"Section: " + self.encodeInt(len(output)) + "\n"
        ret += "\n".join(output)
        return ret
    
    def write(self, file: str):
        if self._hasErrors:
            print("No se pudo escribir el archivo debido a que contiene errores")
            return
        with open(file, "w") as out:
            out.write(self.encodeLabels("Text", self._textLabels))
            out.write(self.encodeLabels("Data", self._dataLabels))
            
            out.write(self.encodeSectionOutput("Text", self._textOutput))
            out.write("\n")
            out.write(self.encodeSectionOutput("Data", self._dataOutput))
            
current_file = ""
lastNewLinePos = 0

#instruction mappea un lexema de instruccion a:
# (tipo_parametros, codigo_base, [largo_parametros])
#ej add (ParamType.rrr, 0x0000000000001, [4, 4, 4])

INSTRUCTION: dict[str, tuple[ParamType, int, list[int]]] = {
    "NOP":      (ParamType._,   0x0000000000000000, []),
    "HLT":      (ParamType._,   0xFFFFFFFFFFFFFFFF, []),
    "JMP":      (ParamType.i,   0x01,               [56]),
    "JMPZ":     (ParamType.i,   0x02,               [56]),
    "JMPNZ":    (ParamType.i,   0x03,               [56]),
    "JMPN":     (ParamType.i,   0x04,               [56]),
    "JMPNN":    (ParamType.i,   0x05,               [56]),
    "JMPOVR":   (ParamType.i,   0x06,               [56]),
    "JMPUND":   (ParamType.i,   0x07,               [56]),
    "JMPNORZ":  (ParamType.i,   0x08,               [56]),
    "JMPNANDZ": (ParamType.i,   0x09,               [56]),
    "JMPR":     (ParamType.r,   0x11,               [4,52]),
    "LOADMEM":  (ParamType.rr,  0x0A,               [4, 4, 48]),
    "LDINT":    (ParamType.ri,  0x9,                [4, 56]),
    "LDFLT":    (ParamType.rf,  0xB,                [4, 56]),
    "MOV":      (ParamType.rr,  0xC0000000000000,   [4, 4]),
    "COMP":     (ParamType.rr,  0x00000000000021,   [4, 4]),
    "NOT":      (ParamType.rr,  0x00000000F00340,   [4, 4]),
    "SHFTL":    (ParamType.rr,  0x00000000F00350,   [4, 4]),
    "SHFTR":    (ParamType.rr,  0x00000000F00360,   [4, 4]),
    "ABVAL":    (ParamType.rr,  0x00000000000041,   [4, 4]),
    "CHNSGN":   (ParamType.rr,  0x00000000000042,   [4, 4]),
    "CHNINT":   (ParamType.rr,  0x00000000000043,   [4, 4]),
    "CHNFLT":   (ParamType.rr,  0x00000000000044,   [4, 4]),
    "ADD":      (ParamType.rrr, 0x0000000000001,    [4, 4, 4]),
    "SUB":      (ParamType.rrr, 0x0000000000002,    [4, 4, 4]),
    "MUL":      (ParamType.rrr, 0x0000000000003,    [4, 4, 4]),
    "DIV":      (ParamType.rrr, 0x0000000000004,    [4, 4, 4]),
    "FADD":     (ParamType.rrr, 0x0000000000011,    [4, 4, 4]),
    "FSUB":     (ParamType.rrr, 0x0000000000012,    [4, 4, 4]),
    "FMUL":     (ParamType.rrr, 0x0000000000013,    [4, 4, 4]),
    "FDIV":     (ParamType.rrr, 0x0000000000014,    [4, 4, 4]),
    "AND":      (ParamType.rrr, 0x0000000000031,    [4, 4, 4]),
    "OR":       (ParamType.rrr, 0x0000000000032,    [4, 4, 4]),
    "XOR":      (ParamType.rrr, 0x0000000000033,    [4, 4, 4]),
    "PUSH":     (ParamType.r,   0x000000000000009,  [4]),
    "POP":      (ParamType.r,   0x00000000000000A,  [4]),
    "DEC":      (ParamType.r,   0x000000000000011,  [4]),
    "INC":      (ParamType.r,   0x000000000000012,  [4]),
    "STOR":     (ParamType.rr,  0x8,                [4, 4, 52]),
    "STRINT":   (ParamType.ri,  0xA,                [4, 56]),
    "STRFLT":   (ParamType.rf,  0xE,                [4, 56]),
}

tokens = [
    "FLOAT",
    "INT",
    "INSTEND",
    "REG",
    "INST",
    "ID",
    "LBL_DEF",
    "SECTION"
]

states = (
    ("label", "exclusive"),
)

literals = [",", ":"]

t_ignore = " \t"

def t_FLOAT(t):
    r"(?:(?P<sign>-)[ \t]*)?(?P<number>\d+\.\d+([Ee][+-]?\d+)?)"
    sign = "" if t.lexer.lexmatch.group("sign") == None else "-"
    t.value = float(sign + t.lexer.lexmatch.group("number"))
    return t

def t_INT(t):
    r"(?i:(?:(?P<sign>-)[ \t]*)?(?P<number>0(?:X[\dA-F]+|O[0-7]+|B[01]+)|\d+))"
    sign = "" if t.lexer.lexmatch.group("sign") == None else "-"
    num = t.lexer.lexmatch.group("number")
    prefix = {
        "0x": 16,
        "0o": 8,
        "0b": 2
    }
    if len(num) > 2:
        base = prefix.get(num[:2], 10)
    else: base = 10
    t.value = int(sign + num, base)
    return t

def t_error(t):
    print(f"Símbolo inesperado '{repr(t.value[0])}' en {current_file}:{t.lexer.lineno}:{t.lexer.lexpos-lastNewLinePos}")
    t.lexer.skip(1)

t_label_ignore = " \t"

def t_begin_label(t):
    r"{"
    t.lexer.begin("label")
    
def t_label_end(t):
    r"}"
    t.lexer.begin("INITIAL")

def t_label_error(t):
    print(f"Símbolo inesperado '{repr(t.value[0])}' en {current_file}:{t.lexer.lineno}:{t.lexer.lexpos-lastNewLinePos}")
    t.lexer.skip(1)

def t_label_nwln(t):
    r"\n+"
    global lastNewLinePos
    t.lexer.lineno += len(t.value)
    lastNewLinePos = t.lexer.lexpos - 1

def t_label_eof(t):
    print(f"Error en {current_file}:{t.lexer.lineno}:{t.lexer.lexpos-lastNewLinePos}: final de archivo alcanzado antes de cerrar etiqueta")
    return None

t_label_LBL_DEF = r"\w[\d\w]*"


def t_ID(t):
    r"\w[\w\d]*"
    val = REGISTERS.get(t.value.upper(), None)
    if val != None:
        t.value = val
        t.type = "REG"
    elif t.value.upper() in INSTRUCTION:
        t.value = t.value.upper()
        t.type = "INST"
    elif t.value.upper() in ["TEXT", "DATA"]:
        t.value = t.value.upper()
        t.type = "SECTION"
    return t
        
def t_INSTEND(t):
    r";|;?(?:\s*\n|\s*\#.*(?:\n|$)|\s+$)+"
    global lastNewLinePos
    newLines = t.value.count("\n")
    t.lexer.lineno += newLines
    if newLines > 0: lastNewLinePos = t.lexer.lexpos - 1
    t.value = ";"
    return t

def main():
    if len(sys.argv) < 3:
        print("Uso: python assembly.py <archivo_asm> <archivo_salida.o> [b|bin|binary|hex|hexadecimal]")
        sys.exit(1)
    asm_file = sys.argv[1]
    out_file = sys.argv[2]
    
    format = sys.argv[3] if len(sys.argv) > 3 else "b"

    global current_file
    current_file = asm_file
    try:
        with open(asm_file, 'r') as f:
            lines = f.read()
    except FileNotFoundError:
        print(f"No se pudo encontrar el archivo {asm_file}")
        return
    
    lexer = lex.lex()
    lexer.input(lines)
    builder = Builder(format)
    last_pos = f"{asm_file}:{1}:{1}"
    while tok := lexer.token():
        # if tok.type in ["INST", ","]: tok.value
        # elif tok.type == "LBL_DEF":
        #     saveLabel(tok.value)
        # print(f"Procesando <{tok.type}> : \"{tok.value}\"")
        pos = f"{asm_file}:{lexer.lineno}:{lexer.lexpos - lastNewLinePos}"
        if tok.type == "INST":
            builder.checkExpected(last_pos)
            builder.instruction(tok.value, pos)
        elif tok.type in ["REG", "INT", "FLOAT", "ID"]:
            builder.checkExpected(last_pos)
            builder.parameter(tok.type, tok.value, pos)
        elif tok.value == ";":
            builder.instructionEnd(last_pos)
            builder.checkExpected(last_pos)
        elif tok.value in literals:
            builder.literal(tok.value, last_pos)
        elif tok.type == "SECTION":
            builder.checkExpected(last_pos)
            builder.section(tok.value, pos)
        elif tok.type == "LBL_DEF":
            builder.checkExpected(last_pos)
            builder.labelDef(tok.value, pos)
        last_pos = pos
    if builder._inst: builder.instructionEnd(last_pos)
    builder.write(out_file)
        
#=======================#
#       GUI API         #
#=======================#

class Assembler:

    def __init__(self, readable="hex"):
        self.readable = readable

    def assemble_text_as_binary(self, text: str) -> list[str]:
        builder = self.assemble_text(text)

        output = []
        for word in builder._textOutput:
            output.append(f"0b{word:064b}")

        return output

    def assemble_text_as_object(self, text: str) -> list[str]:
        builder = self.assemble_text(text)

        # Forzar modo legible (IMPORTANTE)
        builder._format = builder._readableModes["dec"]

        output = ""

        output += builder.encodeLabels()
        output += builder.encodeText()
        output += builder.encodeData()

        # convertir a lista de líneas (lo que espera tu GUI)
        return [line for line in output.splitlines() if line.strip()]

    def assemble_text(self, text: str) -> Builder:
        global lastNewLinePos, current_file

        current_file = "<input>"
        lastNewLinePos = 0

        lexer = lex.lex()
        lexer.input(text)

        builder = Builder(self.readable)
        last_pos = "<input>:1:1"

        while tok := lexer.token():
            pos = f"<input>:{lexer.lineno}:{lexer.lexpos - lastNewLinePos}"

            if tok.type == "INST":
                builder.checkExpected(last_pos)
                builder.instruction(tok.value, pos)

            elif tok.type in ["REG", "INT", "FLOAT", "ID"]:
                builder.checkExpected(last_pos)
                builder.parameter(tok.type, tok.value, pos)

            elif tok.value == ";":
                builder.instructionEnd(last_pos)
                builder.checkExpected(last_pos)

            elif tok.value in literals:
                builder.literal(tok.value, last_pos)

            elif tok.type == "SECTION":
                builder.checkExpected(last_pos)
                builder.section(tok.value, pos)

            elif tok.type == "LBL_DEF":
                builder.checkExpected(last_pos)
                builder.labelDef(tok.value, pos)

            last_pos = pos

        if builder._inst:
            builder.instructionEnd(last_pos)

        if builder._hasErrors:
            raise Exception("Errores en ensamblado")

        return builder

if __name__ == "__main__":
    main()
