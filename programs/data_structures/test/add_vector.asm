# Debe ser enlazado con vector.o y heap.o

TEXT:
LDINT   R1, 1
LDINT   RE, ret
PUSH    RE
JMP     vec_new
{ret}

POP     RE
PUSH RA

#insertar 15
LOADMEM R1, SP
LDINT   R2, 15
LDINT   RE, ret_0
PUSH    RE
JMP     vec_push
{ret_0}
POP     RE

#insertar 42
LOADMEM R1, SP
LDINT   R2, 42
LDINT   RE, ret_1
PUSH    RE
JMP     vec_push
{ret_1}
POP     RE

#insertar 32
LOADMEM R1, SP
LDINT   R2, 32
LDINT   RE, ret_2
PUSH    RE
JMP     vec_push
{ret_2}
POP     RE

#insertar 63
LOADMEM R1, SP
LDINT   R2, 63
LDINT   RE, ret_3
PUSH    RE
JMP     vec_push
{ret_3}
POP     RE

#insertar 12
LOADMEM R1, SP
LDINT   R2, 12
LDINT   RE, ret_4
PUSH    RE
JMP     vec_push
{ret_4}
POP     RE

#sumar numeros dentro vector
LDINT   RE, 0
PUSH    RE          #para suma
PUSH    RE          #para indice

{while}
LOADMEM R2, SP
#i++
INC     R2
STOR    R2, SP
DEC     R2

INC     SP
INC     SP
LOADMEM R1, SP
LOADMEM R3, R1      #espacio usado
DEC     SP
DEC     SP
COMP    R2, R3
JMPZ    end_while

PUSH    R2

#llamado get
LDINT   RE, ret_5
PUSH    RE
JMP     vec_get
{ret_5}
POP     RE

POP     R2
LDINT   R5, 5
COMP    R2, R5
JMPNZ   ignore
{ignore}

INC     SP
LOADMEM RD, SP
ADD     RD, RD, RA
STOR    RD, SP
DEC     SP

JMP while

{end_while}
POP     RD          #indice
POP     RE          #suma
HLT

POP RA

MOV     R1, RA
LOADMEM R2, RA
INC     RA
LOADMEM R3, RA
INC     RA
LOADMEM R4, RA
LOADMEM R5, R4

HLT