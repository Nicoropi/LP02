#ESTANDARD DE LLAMADO DE FUNCIONES ----------------------------------------------------------------

#en general se declaran las funciones despues del cuerpo principal de instrucciones
# si se declaran antes se debe añadir un salto al inicio del cuerpo antes de las funciones
#los registros R1-R5 son usados como parametros de la funcion
#si hace falta pasar argumentos extra, pasar por el stack
#una vez pasados los argumentos pasar direccion de retorno al stack
#los registros RA-RE son volatiles, es decir pueden  cambiar entre llamados a funciones
#el registro RA se toma como el valor de retorno
#los registros RB y SP deben retornar a su valor original una vez termine la funcion
# por esto despues de retornar se debe sacar del stack la direccion de retorno y argumentos

#EJECUCION DEL PROGRAMA ---------------------------------------------------------------------------

#paso de valores a funcion. En este caso solo un argumento en R1
LDINT   R1, 20

#llamado de la funcion
LDINT   RC, ret_1       #cargar direccion de retorno en RC
PUSH    RC              #empujar direccion de retorno al stack
#tambien se puede con: DEC SP; STOR SP, RC;

#saltar a la funcion
JMP     func

#direccion de retorno
{ret_1}
INC     SP              #sacar direccion de retorno del stack
#tambien se puede con: POP [Registro_basura]

HLT                     #IMPORTANTE: terminar programa antes de que pase a las funciones declaradas

#DEFINICION DE LA FUNCION -------------------------------------------------------------------------

{func}
    #simplemente toma el valor de R1 y le suma uno para retornar en RA
    MOV     RA, R1
    INC     RA

    #retorno al procedimiento anterior desde la funcion
    LOADMEM RB, SP
    JMPR    RB
