#Programa de ejemplo que realiza la suma del arreglo A con A_len elementos
data:
{A_len}
5
{A}
100,200,300,400,500
text:
LDINT   RA, A
LDINT   RB, A_len
LDINT   RC, 0
LDINT   RE, 0

{while}
COMP    RB, RC
JMPZ    end_while

LOADMEM RD, RA
ADD     RE, RD, RE

INC     RC
INC     RA

JMP     while

{end_while}
HLT