WORD_MASK = (1 << 64) - 1

SIGN_MASK = 1 << 63
EXP_MASK  = ((1 << 11) - 1) << 52
MANT_MASK = (1 << 52) - 1

BIAS = 1023 # 2^(k−1)−1 where k = 11


#   Basic methods

def fextract(num):
    sign = (num >> 63) & 0x1
    exp  = (num >> 52) & 0x7FF
    mant = num & MANT_MASK

    if exp != 0:
        mant |= (1 << 52)

    return sign, exp, mant

def fpack(sign, exp, mant):
    mant &= MANT_MASK
    result = ((sign & 0x1) << 63) | ((exp & 0x7FF) << 52) | mant

    return result & WORD_MASK

def falign(expA, mantA, expB, mantB):
    if expA > expB:
        shift = expA - expB
        mantB >>= shift
        expB = expA
    elif expB > expA:
        shift = expB - expA
        mantA >>= shift
        expA = expB

    return expA, mantA, mantB

def fnormalize(exp, mant):
    if mant >= (1 << 53):
        mant >>= 1
        exp += 1

    while mant > 0 and mant < (1 << 52):
        mant <<= 1
        exp -= 1

    return exp, mant

# Basic operations

def fadd(a, b):
    signA, expA, mantA = fextract(a)
    signB, expB, mantB = fextract(b)

    exp, mantA, mantB = falign(expA, mantA, expB, mantB)

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

    exp, mant = fnormalize(exp, mant)
    return fpack(sign, exp, mant)

def fsub(a, b):
    b ^= (1 << 63)
    return fadd(a, b)

def fmul(a, b):
    signA, expA, mantA = fextract(a)
    signB, expB, mantB = fextract(b)

    sign = signA ^ signB # signA XOR signB
    exp = expA + expB - BIAS

    mant = (mantA * mantB) >> 52
    exp, mant = fnormalize(exp, mant)
    return fpack(sign, exp, mant)

def fdiv(a, b):
    signA, expA, mantA = fextract(a)
    signB, expB, mantB = fextract(b)

    if mantB == 0:
        raise Exception("Divide by zero")

    sign = signA ^ signB # signA XOR signB
    exp = expA - expB + BIAS

    mant = (mantA << 52) // mantB
    exp, mant = fnormalize(exp, mant)
    return fpack(sign, exp, mant)

# Convertion

def int_to_float(n):
    if n == 0:
        return 0

    sign = 0
    if n < 0:
        sign = 1
        n = -n

    # Position of the Most Significant Bit
    msb = n.bit_length() - 1
    exp = msb + BIAS
    mant = n << (52 - msb)

    return fpack(sign, exp, mant)