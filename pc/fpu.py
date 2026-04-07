WORD_MASK = (1 << 64) - 1

SIGN_MASK = 1 << 63
EXP_MASK  = ((1 << 11) - 1) << 52
MANT_MASK = (1 << 52) - 1

BIAS = 1023


class FPU:

    def __init__(self, registers):
        self.reg = registers

    # ------------------------
    # BASIC METHODS
    # ------------------------

    def fextract(self, num):
        sign = (num >> 63) & 0x1
        exp  = (num >> 52) & 0x7FF
        mant = num & MANT_MASK

        if exp != 0:
            mant |= (1 << 52)

        return sign, exp, mant

    def fpack(self, sign, exp, mant):
        mant &= MANT_MASK
        return ((sign & 1) << 63) | ((exp & 0x7FF) << 52) | mant

    def falign(self, expA, mantA, expB, mantB):
        if expA > expB:
            mantB >>= (expA - expB)
            return expA, mantA, mantB
        elif expB > expA:
            mantA >>= (expB - expA)
            return expB, mantA, mantB
        return expA, mantA, mantB

    def fnormalize(self, exp, mant):
        if mant == 0:
            return 0, 0

        while mant >= (1 << 53):
            mant >>= 1
            exp += 1

        while mant < (1 << 52):
            mant <<= 1
            exp -= 1

        return exp, mant

    # ------------------------
    # FLAGS
    # ------------------------

    def update_flags(self, result):
        sign, exp, mant = self.fextract(result)

        self.reg.flags["Z"] = int(result == 0)
        self.reg.flags["N"] = sign

        # overflow
        self.reg.flags["D"] = int(exp >= 2047)

        # underflow
        self.reg.flags["U"] = int(exp == 0 and mant != 0)

    # ------------------------
    # FLOAT OPERATIONS
    # ------------------------

    def fadd(self, a, b):
        signA, expA, mantA = self.fextract(a)
        signB, expB, mantB = self.fextract(b)

        exp, mantA, mantB = self.falign(expA, mantA, expB, mantB)

        if signA == signB:
            mant = mantA + mantB
            sign = signA
        else:
            if mantA >= mantB:
                mant = mantA - mantB
                sign = signA
            else:
                mant = mantB - mantA
                sign = signB

        exp, mant = self.fnormalize(exp, mant)

        result = self.fpack(sign, exp, mant)
        self.update_flags(result)
        return result

    def fsub(self, a, b):
        b ^= (1 << 63)
        return self.add(a, b)

    def fmul(self, a, b):
        signA, expA, mantA = self.fextract(a)
        signB, expB, mantB = self.fextract(b)

        sign = signA ^ signB
        exp = expA + expB - BIAS

        mant = (mantA * mantB) >> 52
        exp, mant = self.fnormalize(exp, mant)

        if exp >= 2047:
            result = self.fpack(sign, 2047, 0)
        else:
            result = self.fpack(sign, exp, mant)

        self.update_flags(result)
        return result

    def fdiv(self, a, b):
        signA, expA, mantA = self.fextract(a)
        signB, expB, mantB = self.fextract(b)

        if mantB == 0:
            raise Exception("Divide by zero")

        sign = signA ^ signB
        exp = expA - expB + BIAS

        mant = (mantA << 52) // mantB
        exp, mant = self.fnormalize(exp, mant)

        result = self.fpack(sign, exp, mant)
        self.update_flags(result)
        return result

    # ------------------------
    # CONVERSIONS
    # ------------------------

    def int_to_float(self, n):
        if n == 0:
            return 0

        sign = 0
        if n < 0:
            sign = 1
            n = -n

        msb = n.bit_length() - 1
        exp = msb + BIAS

        mant = n << (52 - msb)
        mant &= MANT_MASK

        result = self.fpack(sign, exp, mant)
        self.update_flags(result)
        return result

    def float_to_int(self, x):
        sign, exp, mant = self.fextract(x)

        if exp == 0:
            return 0

        shift = exp - BIAS - 52
        if shift >= 0:
            val = mant << shift
        else:
            val = mant >> (-shift)

        if sign:
            val = -val

        result = val & WORD_MASK
        self.update_flags(result)
        return result