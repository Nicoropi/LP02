WORD_BITS   = 64
WORD_MASK   = (1 << WORD_BITS) - 1
HLT_WORD    = WORD_MASK
NOP_WORD    = 0

# Señales del Bus de Control
CTRL_MEM_READ  = 0   # par  -> lectura
CTRL_MEM_WRITE = 1   # impar -> escritura


class CPU:

    # Mapa de codigos de 4 bits -> nombre de registro
    register_map = {
        0b0001: "PC",  0b0010: "SP",  0b0011: "BP",  0b0100: "IR",
        0b0101: "RA",  0b0110: "RB",  0b0111: "RC",  0b1000: "RD",
        0b1001: "RE",  0b1010: "R1",  0b1011: "R2",  0b1100: "R3",
        0b1101: "R4",  0b1110: "R5",
    }

    def __init__(self, ram, registers, alu):
        self.ram = ram
        self.reg = registers
        self.alu = alu
        self.running = True
        self.cycle_count = 0

    # Simulacion del Bus de Direcciones + Bus de Control (MemRead)
    def read_memory(self, address):
        """MAR <- address, señal MemRead, dato -> MDR."""
        self.reg.MAR = address & WORD_MASK
        data = self.ram.request(
            data=0,
            direction=self.reg.MAR,
            control=CTRL_MEM_READ
        )
        self.reg.MDR = data & WORD_MASK
        return self.reg.MDR

    # Simulacion del Bus de Direcciones + Datos + Control (MemWrite)
    def write_memory(self, address, data):
        """MAR <- address, MDR <- data, señal MemWrite."""
        self.reg.MAR = address & WORD_MASK
        self.reg.MDR = data & WORD_MASK
        self.ram.request(
            data=self.reg.MDR,
            direction=self.reg.MAR,
            control=CTRL_MEM_WRITE
        )

    # Bus interno del CPU — lectura/escritura de registros
    def get_reg(self, code):
        name = self.register_map.get(code)
        if name is None:
            return 0
        if name in self.reg.general:
            return self.reg.general[name]
        return getattr(self.reg, name, 0)

    def set_reg(self, code, value):
        name = self.register_map.get(code)
        if name is None:
            return
        value = value & WORD_MASK
        if name in self.reg.general:
            self.reg.general[name] = value
        else:
            setattr(self.reg, name, value)

    # FETCH — busqueda de instruccion
    # IR <- MEM[PC], PC <- PC + 1
    def fetch(self):
        self.reg.MAR = self.reg.PC
        instr = self.read_memory(self.reg.MAR)
        self.reg.IR = instr
        self.reg.PC += 1

    # EXECUTE — decodificacion y ejecucion (41 instrucciones)
    # Usa mascaras de bits (>>, &) para extraer opcodes y operandos.
    # Orden: mas especifico -> mas generico para evitar colisiones.
    def execute(self):
        instr = self.reg.IR

        # 1. COINCIDENCIA EXACTA DE 64 BITS
        # NOP: todo ceros — no hace nada
        if instr == NOP_WORD:
            return

        # HLT: todo unos — detiene la CPU
        if instr == HLT_WORD:
            self.running = False
            return

        # 2. PREFIJO DE 8 BITS — bits [63:56]
        #    Saltos (formato J) y LOAD MEM
        opcode8 = (instr >> 56) & 0xFF
        jump_addr = instr & 0x00FFFFFFFFFFFFFF  # 56 bits de direccion

        # JMP {dir} — salto incondicional, PC <- dir
        if opcode8 == 0x01:
            self.reg.PC = jump_addr
            return

        # JMPZ — salta si Z=1
        if opcode8 == 0x02:
            if self.reg.flags["Z"] == 1:
                self.reg.PC = jump_addr
            return

        # JMPNZ — salta si Z=0
        if opcode8 == 0x03:
            if self.reg.flags["Z"] == 0:
                self.reg.PC = jump_addr
            return

        # JMPN — salta si N=1 (negativo)
        if opcode8 == 0x04:
            if self.reg.flags["N"] == 1:
                self.reg.PC = jump_addr
            return

        # JMPNN — salta si N=0 (no negativo)
        if opcode8 == 0x05:
            if self.reg.flags["N"] == 0:
                self.reg.PC = jump_addr
            return

        # JMP OVR — salta si D=1 (overflow)
        if opcode8 == 0x06:
            if self.reg.flags["D"] == 1:
                self.reg.PC = jump_addr
            return

        # JMP UND — salta si U=1 (underflow)
        if opcode8 == 0x07:
            if self.reg.flags["U"] == 1:
                self.reg.PC = jump_addr
            return

        # JMP NORZ — salta si N=0 AND Z=0
        if opcode8 == 0x08:
            if not (self.reg.flags["N"] or self.reg.flags["Z"]):
                self.reg.PC = jump_addr
            return

        # JMP NANDZ — salta si N=0 OR Z=0
        if opcode8 == 0x09:
            if not (self.reg.flags["N"] and self.reg.flags["Z"]):
                self.reg.PC = jump_addr
            return

        # LOAD MEM X, Y — X <- MEM[Y]
        # Binario: 0000 1010 xxxx yyyy 0...0
        if opcode8 == 0x0A:
            reg_x = (instr >> 52) & 0xF
            reg_y = (instr >> 48) & 0xF
            value = self.read_memory(self.get_reg(reg_y))
            self.set_reg(reg_x, value)
            return

        # 3. PREFIJO DE 4 BITS — bits [63:60]
        #    STOR, inmediatos, MOV, STOR FLOAT
        opcode4 = (instr >> 60) & 0xF

        # STOR X, Y — MEM[Y] <- X
        # Binario: 1000 xxxx yyyy 0...0
        if opcode4 == 0x8:
            reg_x = (instr >> 56) & 0xF
            reg_y = (instr >> 52) & 0xF
            self.write_memory(self.get_reg(reg_y), self.get_reg(reg_x))
            return

        # LOAD INT X, VALUE — X <- VALUE (inmediato con signo)
        # Binario: 1001 xxxx vvvv...vvvv (56 bits)
        if opcode4 == 0x9:
            reg_x = (instr >> 56) & 0xF
            imm56 = instr & 0x00FFFFFFFFFFFFFF
            if imm56 & (1 << 55):  # extension de signo
                imm56 |= 0xFF00000000000000
            self.set_reg(reg_x, imm56)
            return

        # STORI X, VALUE — MEM[X] <- VALUE (store inmediato)
        # Binario: 1010 xxxx vvvv...vvvv
        if opcode4 == 0xA:
            reg_x = (instr >> 56) & 0xF
            imm56 = instr & 0x00FFFFFFFFFFFFFF
            if imm56 & (1 << 55):
                imm56 |= 0xFF00000000000000
            self.write_memory(self.get_reg(reg_x), imm56)
            return

        # LOAD FLOAT X, VALUE — X <- VALUE (punto fijo 32.32)
        # Binario: 1011 xxxx vvvv...vvvv
        if opcode4 == 0xB:
            reg_x = (instr >> 56) & 0xF
            imm56 = instr & 0x00FFFFFFFFFFFFFF
            if imm56 & (1 << 55):
                imm56 |= 0xFF00000000000000
            self.set_reg(reg_x, imm56)
            return

        # MOV X, Y — X <- Y
        # Binario: 1100 0...0 xxxx yyyy
        if opcode4 == 0xC:
            reg_x = (instr >> 4) & 0xF
            reg_y = instr & 0xF
            self.set_reg(reg_x, self.get_reg(reg_y))
            return

        # STOR FLOAT — MEM[X] <- VALUE (float inmediato)
        # Binario: 1110 xxxx vvvv...vvvv
        if opcode4 == 0xE:
            reg_x = (instr >> 56) & 0xF
            imm56 = instr & 0x00FFFFFFFFFFFFFF
            if imm56 & (1 << 55):
                imm56 |= 0xFF00000000000000
            self.write_memory(self.get_reg(reg_x), imm56)
            return

        # SUBCODES EN BITS BAJOS (bits altos = 0)
        # UTILIDADES — byte [15:8] = 0x41..0x44
        util_op = (instr >> 8) & 0xFF

        if util_op == 0x41 and (instr >> 16) == 0:
            # ABVAL X, Y — X <- |Y|
            reg_x = (instr >> 4) & 0xF
            reg_y = instr & 0xF
            val = self.get_reg(reg_y)
            if val & (1 << 63):
                result = (-(val - (1 << 64))) & WORD_MASK
            else:
                result = val
            self.alu.update_flags(result)
            self.set_reg(reg_x, result)
            return

        if util_op == 0x42 and (instr >> 16) == 0:
            # CHNG SIG X, Y — X <- -Y
            reg_x = (instr >> 4) & 0xF
            val = self.get_reg(instr & 0xF)
            result = ((~val) + 1) & WORD_MASK
            self.alu.update_flags(result)
            self.set_reg(reg_x, result)
            return

        if util_op == 0x43 and (instr >> 16) == 0:
            # CHNG INT X, Y — X <- int(Y) (float -> entero)
            reg_x = (instr >> 4) & 0xF
            val = self.get_reg(instr & 0xF)
            int_part = (val >> 32) & 0xFFFFFFFF
            if int_part & (1 << 31):
                int_part |= 0xFFFFFFFF00000000
            result = int_part & WORD_MASK
            self.alu.update_flags(result)
            self.set_reg(reg_x, result)
            return

        if util_op == 0x44 and (instr >> 16) == 0:
            # CHNG FLOAT X, Y — X <- float(Y) (entero -> float)
            reg_x = (instr >> 4) & 0xF
            val = self.get_reg(instr & 0xF)
            result = (val << 32) & WORD_MASK
            self.alu.update_flags(result)
            self.set_reg(reg_x, result)
            return

        # COMP X, Y — actualiza FLAGS, no guarda resultado
        #     Byte [15:8] = 0x21
        #     ANTES de aritmetica RRR (comparte bits [15:12]=0x2 con SUB)
        if (instr >> 8) == 0x21 and (instr >> 16) == 0:
            reg_x = (instr >> 4) & 0xF
            reg_y = instr & 0xF
            self.alu.comp(self.get_reg(reg_x), self.get_reg(reg_y))
            return

        # LOGICA + SHIFTS — nibble [19:16] = 0x3
        if (instr >> 16) & 0xF == 0x3 and ((instr >> 24) & 0xF) == 0:
            logic_id  = (instr >> 12) & 0xF
            marker_32 = (instr >> 28) & 0xF

            if logic_id == 0x1 and marker_32 == 0:
                # AND X, W, Y
                rx = (instr >> 8) & 0xF
                result = self.alu.and_op(
                    self.get_reg((instr >> 4) & 0xF), self.get_reg(instr & 0xF))
                self.set_reg(rx, result)
                return

            if logic_id == 0x2 and marker_32 == 0:
                # OR X, W, Y
                rx = (instr >> 8) & 0xF
                result = self.alu.or_op(
                    self.get_reg((instr >> 4) & 0xF), self.get_reg(instr & 0xF))
                self.set_reg(rx, result)
                return

            if logic_id == 0x3 and marker_32 == 0:
                # XOR X, W, Y
                rx = (instr >> 8) & 0xF
                result = self.alu.xor_op(
                    self.get_reg((instr >> 4) & 0xF), self.get_reg(instr & 0xF))
                self.set_reg(rx, result)
                return

            if logic_id == 0x4 and marker_32 == 0xF:
                # NOT X, Y
                rx = (instr >> 4) & 0xF
                result = self.alu.not_op(self.get_reg(instr & 0xF))
                self.set_reg(rx, result)
                return

            if logic_id == 0x5 and marker_32 == 0xF:
                # SHIFT L X, Y — X <- Y << 1
                rx = (instr >> 4) & 0xF
                result = self.alu.shift_left(self.get_reg(instr & 0xF), 1)
                self.set_reg(rx, result)
                return

            if logic_id == 0x6 and marker_32 == 0xF:
                # SHIFT R X, Y — X <- Y >> 1
                rx = (instr >> 4) & 0xF
                result = self.alu.shift_right(self.get_reg(instr & 0xF), 1)
                self.set_reg(rx, result)
                return

        # ARITMETICA FLOTANTE — byte [23:16] = 0x01
        if (instr >> 16) & 0xFF == 0x01 and (instr >> 24) == 0:
            sub_op = (instr >> 12) & 0xF
            rx = (instr >> 8) & 0xF
            a = self.get_reg((instr >> 4) & 0xF)
            b = self.get_reg(instr & 0xF)

            if sub_op == 0x1:
                result = self.alu.add_float(a, b)
            elif sub_op == 0x2:
                result = self.alu.sub_float(a, b)
            elif sub_op == 0x3:
                result = self.alu.mul_float(a, b)
            elif sub_op == 0x4:
                result = self.alu.div_float(a, b)
            else:
                return
            self.set_reg(rx, result)
            return

        # PUSH / POP — nibble [7:4]
        lo_nib = (instr >> 4) & 0xF

        if lo_nib == 0x9 and (instr >> 8) == 0:
            # PUSH X — SP--, MEM[SP] <- X
            rx = instr & 0xF
            self.reg.SP = (self.reg.SP - 1) & WORD_MASK
            self.write_memory(self.reg.SP, self.get_reg(rx))
            return

        if lo_nib == 0xA and (instr >> 8) == 0:
            # POP X — X <- MEM[SP], SP++
            rx = instr & 0xF
            self.set_reg(rx, self.read_memory(self.reg.SP))
            self.reg.SP = (self.reg.SP + 1) & WORD_MASK
            return

        # INC / DEC — byte [11:4]
        lo_byte = (instr >> 4) & 0xFF

        if lo_byte == 0x11 and (instr >> 12) == 0:
            # DEC X — X <- X - 1
            rx = instr & 0xF
            self.set_reg(rx, self.alu.sub(self.get_reg(rx), 1))
            return

        if lo_byte == 0x12 and (instr >> 12) == 0:
            # INC X — X <- X + 1
            rx = instr & 0xF
            self.set_reg(rx, self.alu.add(self.get_reg(rx), 1))
            return

        # ARITMETICA ENTERA RRR — nibble [15:12]
        sub_op = (instr >> 12) & 0xF

        if sub_op in (0x1, 0x2, 0x3, 0x4) and (instr >> 16) == 0:
            rx = (instr >> 8) & 0xF
            a = self.get_reg((instr >> 4) & 0xF)
            b = self.get_reg(instr & 0xF)

            if sub_op == 0x1:
                result = self.alu.add(a, b)     # ADD
            elif sub_op == 0x2:
                result = self.alu.sub(a, b)     # SUB
            elif sub_op == 0x3:
                result = self.alu.mul(a, b)     # MUL
            elif sub_op == 0x4:
                result = self.alu.div(a, b)     # DIV

            self.set_reg(rx, result)
            return

        print(f"  [WARN] Instruccion no reconocida: 0x{instr:016X}")

    # RUN — ciclo Fetch-Decode-Execute hasta HLT
    def run(self):
        self.running = True
        self.cycle_count = 0
        while self.running:
            self.cycle_count += 1
            self.fetch()
            self.execute()

    # Depuracion
    def dump_registers(self):
        """Imprime el estado de todos los registros y FLAGS."""
        print("\n" + "=" * 60)
        print("  ESTADO FINAL DE LOS REGISTROS")
        print("=" * 60)
        for label in ("PC", "SP", "BP", "IR", "MAR", "MDR"):
            val = getattr(self.reg, label)
            print(f"  {label:3s} = {val:>20d}  (0x{val:016X})")
        print("  " + "-" * 56)
        for name in ("RA", "RB", "RC", "RD", "RE", "R1", "R2", "R3", "R4", "R5"):
            val = self.reg.general[name]
            print(f"  {name:3s} = {val:>20d}  (0x{val:016X})")
        print("  " + "-" * 56)
        flags_str = "  ".join(f"{k}={v}" for k, v in self.reg.flags.items())
        print(f"  FLAGS: {flags_str}")
        print("=" * 60)
