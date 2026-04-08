LDINT RA, 48
LDINT RB, 18
COMP RA, RB          
JMPZ 10               
JMPN 8
JMP  6      
SUB RA, RA, RB        
JMP 2
SUB RB, RB, RA        
JMP 2
HLT                