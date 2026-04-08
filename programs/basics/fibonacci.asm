LDINT RA, 0 
LDINT RB, 1        
LDINT RC, 10       
LDINT RD, 0        
COMP RC, RD             
JMPNORZ 12
COMP RC, RD            
JMPZ 12      
ADD RE, RA, RB      
MOV RA, RB         
MOV RB, RE             
INC RD             
COMP RC, RD         
JMPNZ 6       
HLT