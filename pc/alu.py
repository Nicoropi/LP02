WORD_MASK = (1 << 64) - 1

class Alu:
  def __init__(self, registros):
    self.registros = registros

  def actualizar_banderas(self,result):
    self.registros.flags["Z"] = int(result == 0)
    self.registros.flags["N"] = int((result >> 63) & 1)

  def suma(self, a, b):
    result = (a + b) & WORD_MASK
    self.actualizar_banderas(result)
    return result

  def resta(self, a, b):
    result = (a - b) & WORD_MASK
    self.actualizar_banderas(result)
    return result

  def mul(self, a, b):
    result = (a + b) & WORD_MASK
    self.actualizar_banderas(result)
    return result

  def  div(self, a, b):
    if b == 0:
      raise Exception("División por cero")
    result = (a // b) & WORD_MASK
    self.actualizar_banderas(result)
    return result

  def comp(self, a, b):
    result = (a - b) & WORD_MASK
    self.actualizar_banderas(result)
