class CPU:

    def __init__(self, ram, registers, alu):
        self.ram = ram
        self.reg = registers
        self.alu = alu
        self.running = True

        self.register_map = {
            0b0001: "PC",
            0b0010: "SP",
            0b0011: "BP",
            0b0100: "IR",
            0b0101: "RA",
            0b0110: "RB",
            0b0111: "RC",
            0b1000: "RD",
            0b1001: "RE",
            0b1010: "R1",
            0b1011: "R2",
            0b1100: "R3",
            0b1101: "R4",
            0b1110: "R5"
        }

    def fetch(self):
        self.reg.MAR = self.reg.PC
        instr = self.ram.request(0, self.reg.MAR, 0)
        self.reg.MDR = instr
        self.reg.IR = instr
        self.reg.PC += 1

    def get_reg(self, code):
        name = self.register_map.get(code)

        if name in self.reg.general:
            return self.reg.general[name]
        else:
            return getattr(self.reg, name)

    def set_reg(self, code, value):
        name = self.register_map.get(code)

        if name in self.reg.general:
            self.reg.general[name] = value
        else:
            setattr(self.reg, name, value)

    def execute(self):

        instr = self.reg.IR

        # Type J (jumps)
        opcode8 = (instr >> 56) & 0xFF

        if opcode8 == 0x01:  # JMP
            address = instr & 0x00FFFFFFFFFFFFFF
            self.reg.PC = address
            return

        if opcode8 == 0x02:  # JMPZ
            if self.reg.flags["Z"] == 1:
                address = instr & 0x00FFFFFFFFFFFFFF
                self.reg.PC = address
            return

        # Type A (operations between reg)
        opcode = (instr >> 12) & 0xFFFF

        if opcode == 0x0001:
            rd = (instr >> 8) & 0xF
            ra = (instr >> 4) & 0xF
            rb = instr & 0xF

            a = self.get_reg(ra)
            b = self.get_reg(rb)
            result = self.alu.add(a, b)
            self.set_reg(rd, result)

        elif opcode == 0x0002:
            rd = (instr >> 8) & 0xF
            ra = (instr >> 4) & 0xF
            rb = instr & 0xF

            a = self.get_reg(ra)
            b = self.get_reg(rb)
            result = self.alu.sub(a, b)
            self.set_reg(rd, result)

        elif opcode == 0xF034:  
            rd = (instr >> 4) & 0xF
            ra = instr & 0xF

            value = self.get_reg(ra)
            result = self.alu.not_op(value)
            self.set_reg(rd, result)

        elif instr == 0xFFFFFFFFFFFFFFFF:
            self.running = False

    def run(self):
        while self.running:
            self.fetch()
            self.execute()
