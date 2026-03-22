import sys

REGISTERS = {
    'PC': 0x1, 'SP': 0x2, 'BP': 0x3, 'IR': 0x4, 'RA': 0x5,
    'RB': 0x6, 'RC': 0x7, 'RD': 0x8, 'RE': 0x9,
    'R1': 0xA, 'R2': 0xB, 'R3': 0xC, 'R4': 0xD, 'R5': 0xE,
}

INSTRUCTION = {
    "NOP":      ["nop", 0x0000000000000000],
    "HLT":      ["nop", 0xFFFFFFFFFFFFFFFF],
    "JMP":      ["jmp", 0x01],
    "JMPZ":     ["jmp", 0x02],
    "JMPNZ":    ["jmp", 0x03],
    "JMPN":     ["jmp", 0x04],
    "JMPNN":    ["jmp", 0x05],
    "JMPOVR":   ["jmp", 0x06],
    "JMPUND":   ["jmp", 0x07],
    "JMPNORZ":  ["jmp", 0x08],
    "JMPNANDZ": ["jmp", 0x09],
    "LOADMEM":  ["r_m", 0xA],
    "LDINT":    ["r_m", 0x9],
    "LDFLT":    ["r_m", 0xB],
    "MOV":      ["r_r", 0xC0000000000000],
    "COMP":     ["r_r", 0x00000000000021],
    "NOT":      ["r_r", 0x00000000F00034],
    "SHFTL":    ["r_r", 0x00000000F00035],
    "SHFTR":    ["r_r", 0x00000000F00036],
    "ABVAL":    ["r_r", 0x00000000000041],
    "CHNSGN":   ["r_r", 0x00000000000042],
    "N2INT":    ["r_r", 0x00000000000043],
    "N2FLT":    ["r_r", 0x00000000000044],
    "ADD":      ["rrr", 0x0000000000001],
    "SUB":      ["rrr", 0x0000000000002],
    "MUL":      ["rrr", 0x0000000000003],
    "DIV":      ["rrr", 0x0000000000004],
    "FADD":     ["rrr", 0x0000000000011],
    "FSUB":     ["rrr", 0x0000000000012],
    "FMUL":     ["rrr", 0x0000000000013],
    "FDIV":     ["rrr", 0x0000000000014],
    "AND":      ["rrr", 0x0000000000031],
    "OR":       ["rrr", 0x0000000000032],
    "XOR":      ["rrr", 0x0000000000033],
    "PUSH":     ["reg", 0x000000000000009],
    "POP":      ["reg", 0x00000000000000A],
    "DEC":      ["reg", 0x000000000000011],
    "INC":      ["reg", 0x000000000000012],

    "STOR": ["m_r", 0x08],
    "STRINT": ["m_m", 0xA],
    "STRFLT": ["m_m", 0xE],
}

def parse_num(tok):
    t = tok.strip()
    if t.startswith("0x") or t.startswith("0X"):
        return int(t, 16)
    return int(t)

def parse_reg(tok):
    t = tok.strip().upper()
    if t not in REGISTERS:
        raise ValueError(f"Registro desconocido: {tok}")
    return REGISTERS[t]

def collect_labels(lines):
    labels = {}
    addr = 0
    for line in lines:
        s = line.split("#", 1)[0].strip()
        if not s:
            continue
        if s.endswith(":"):
            labels[s[:-1]] = addr
            continue
        addr += 1
    return labels

def encode_line(mnemonic, operands, labels):
    mnemonic = mnemonic.upper()
    if mnemonic not in INSTRUCTION:
        raise ValueError(f"Instrucción desconocida: {mnemonic}")
    mode, base = INSTRUCTION[mnemonic]

    # NOP/HLT
    if mnemonic in ("NOP", "HLT"):
        return base
    
    if mode == "jmp":
        word = base << 56
        addr = 0
        
        if operands:
            tok = operands[0]
            addr = labels.get(tok, None) if tok in labels else parse_num(tok)
        word |= addr & ((1 << 64) - 1)
        return word

    if mode == "r_m":
        word = base << 60
        reg = parse_reg(operands[0]) if operands else 0
        mem = 0

        if len(operands) > 1:
            tok = operands[1]
            mem = labels.get(tok, None) if tok in labels else parse_num(tok)

        word |= (reg & 0xF) << 56
        word |= (mem & ((1 << 56) - 1))
        return word

    if mode == "m_r":
        word = base << 56
        mem = parse_num(operands[0]) if operands else 0
        reg = parse_reg(operands[1]) if len(operands) > 1 else 0

        word |= (mem & ((1 << 56) - 1)) << 4
        word |= (reg & 0xF)
        return word

    if mode == "r_r":
        word = base << 8
        r1 = parse_reg(operands[0]) if len(operands) > 0 else 0
        r2 = parse_reg(operands[1]) if len(operands) > 1 else 0
        word |= (r1 & 0xF) << 4
        word |= (r2 & 0xF)
        return word

    if mode == "rrr":
        word = base << 12
        r1 = parse_reg(operands[0])
        r2 = parse_reg(operands[1])
        r3 = parse_reg(operands[2])
        word |= (r1 & 0xF) << 8
        word |= (r2 & 0xF) << 4
        word |= (r3 & 0xF) 
        return word

    if mode == "reg":
        word = base << 4
        r = parse_reg(operands[0])
        word |= (r & 0xF) 
        return word

    if mode == "m_m":
        word = base << 60
        mem = parse_num(operands[0])
        val = parse_num(operands[1])
        word |= (mem & 0x0FFFFFFF) << 32
        word |= (val & 0x0FFFFFFF)
        return word

    raise ValueError(f"Formato no soportado para {mnemonic}")

def main():
    if len(sys.argv) < 3:
        print("Uso: python assembly.py <archivo_asm> <archivo_salida.bin>")
        sys.exit(1)
    asm_file = sys.argv[1]
    out_file = sys.argv[2]

    with open(asm_file, 'r') as f:
        lines = f.readlines()

    labels = collect_labels(lines)
    words = []
    for idx, line in enumerate(lines, 1):
        s = line.split('#', 1)[0].strip()
        if not s: continue
        if s.endswith(':'): continue
        parts = s.replace(',', ' ').split()
        mnemonic = parts[0]
        ops = parts[1:]
        w = encode_line(mnemonic, ops, labels)
        words.append(w)

    with open(out_file, 'w') as fout:
        fout.write("# Assembled from {}\n".format(asm_file))
        for w in words:
            fout.write(f"{w:064b}\n")
    print("Ensamblado generado: {} palabras".format(len(words)))

if __name__ == "__main__":
    main()
