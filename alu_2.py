WORD_MASK = (1 << 64) - 1

MAX_INT = (1 << 63) - 1
MIN_INT = -(1 << 63)

EPSILON = 1 / (1 << 32)


class Alu:
    def __init__(self, registros):
        self.registros = registros

    def update_flags(self, result):
        self.registros.flags["Z"] = int(result == 0)
        self.registros.flags["N"] = int((result >> 63) & 1)

    def check_overflow_int(self, a, b, raw):
        a_sign = (a >> 63) & 1
        b_sign = (b >> 63) & 1
        r_sign = (raw >> 63) & 1
        if a_sign == b_sign and a_sign != r_sign:
            self.registros.flags["D"] = 1
        else:
            self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0

    def check_overflow_float(self, raw_result):
        result = raw_result & WORD_MASK
        integer_part = result >> 32
        if integer_part & (1 << 31):
            integer_part -= (1 << 32)
        if integer_part > (2**31 - 1) or integer_part < -(2**31):
            self.registros.flags["D"] = 1
        else:
            self.registros.flags["D"] = 0
        if integer_part == 0 and result != 0:
            self.registros.flags["U"] = 1
        else:
            self.registros.flags["U"] = 0

    def add(self, a, b):
        result = (a + b) & WORD_MASK
        self.check_overflow_int(a,b,result)
        self.update_flags(result)
        return result

    def sub(self, a, b):
        result = (a - b) & WORD_MASK
        self.check_overflow_int(a,b,result)
        self.update_flags(result)
        return result

    def mul(self, a, b):
        raw = a * b
        if raw > MAX_INT or raw < MIN_INT:
            self.registros.flags["D"] = 1
        else:
            self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        result = raw & WORD_MASK
        self.update_flags(result)
        return result

    def div(self, a, b):
        if b == 0:
            raise Exception("Divide by zero")
        raw = a // b
        if raw > MAX_INT or raw < MIN_INT:
            self.registros.flags["D"] = 1
        else:
            self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        result = raw & WORD_MASK
        self.update_flags(result)
        return result

    def comp(self, a, b):
        result = (a - b) & WORD_MASK
        self.check_overflow_int(a,b,result)
        self.update_flags(result)

    def add_float(self, a, b):
        raw = a + b
        self.check_overflow_float(raw)
        result = raw & WORD_MASK
        self.update_flags(result)
        return result
    
    def sub_float(self, a, b):
        raw = a - b
        self.check_overflow_float(raw)
        result = raw & WORD_MASK
        self.update_flags(result)
        return result

    def mul_float(self, a, b):
        raw = (a * b) >> 32
        self.check_overflow_float(raw)
        result = raw & WORD_MASK
        self.update_flags(result)
        return result

    def div_float(self, a, b):
        if b == 0:
            raise Exception("Divide by zero")
        raw = (a << 32) // b
        self.check_overflow_float(raw)
        result = raw & WORD_MASK
        self.update_flags(result)
        return result

    def and_op(self, a, b):
        result = (a & b) & WORD_MASK
        self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result

    def or_op(self, a, b):
        result = (a | b) & WORD_MASK
        self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result

    def xor_op(self, a, b):
        result = (a ^ b) & WORD_MASK
        self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result

    def not_op(self, a):
        result = (~a) & WORD_MASK
        self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result

    def shift_left(self, a, n):
        a &= WORD_MASK
        raw = a << n
        result = raw & WORD_MASK
        # Overflow:
        original_sign = (a >> 63) & 1
        result_sign = (result >> 63) & 1
        if original_sign != result_sign:
            self.registros.flags["D"] = 1
        else:
            self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result

    def shift_right(self, a, n):
        if a & (1 << 63):
            a_signed = a - (1 << 64)
        else:
            a_signed = a
        raw = a_signed >> n
        result = raw & WORD_MASK
        self.registros.flags["D"] = 0
        self.registros.flags["U"] = 0
        self.update_flags(result)
        return result
