class Registers:
  def __init__(self):
    #Specials
    self.PC = 0
    self.SP = 0
    self.BP = 0
    self.IR = 0
  
    #Registros Generales
    self.general = {"RA": 0, "RB": 0, "RC": 0,"RD": 0, "RE": 0,
            "R1": 0, "R2": 0, "R3": 0,"R4": 0, "R5": 0}
    #Flags
    self.flags = {"N": 0,"Z": 0,"D": 0,"U": 0}
