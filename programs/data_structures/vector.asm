# Debe ser enlazado con heap.o

#MANEJO DE ERRORES:
#para las siguientes funciones se denotara que ocurrio un error con la overflow flag
# o retornando 0 en RA, la segunda solo aplica retornando apuntadores pero la flag siempre aplica

#crea un nuevo vector con n espacios
#retorna posicion de memoria, 0 si falla
#n en R1
{vec_new}
    #reservar espacio
    PUSH    R1          #guardar largo del vector para despues
    #reservar para largo del vector, espacio usado, y apuntador al arreglo
    LDINT   R1, 3       #tenemos que guardar 3 valores
    LDINT   RE, vec_new_return_1
    PUSH    RE
    JMP     malloc  #llamar malloc
    {vec_new_return_1}
    POP     RE #sacar dir retorno

    LOADMEM R1, SP      #recobrar largo del vector
    PUSH    RA  #guardar valor de RA

    #reservar arreglo para los valores
    LDINT   RE, vec_new_return_2
    PUSH    RE
    JMP     malloc  #llamar malloc otra vez
    {vec_new_return_2}
    POP     RE #sacar dir retorno

    POP     RB
    POP     R1 #recobrar largo del vector (por si la funcion lo cambia)

    #revisar si malloc fallo
    LDINT   RE, 0
    COMP    RA, RE      #comparar con RA con 0
    JMPZ    vec_new_end #si es 0 saltar al final de la funcion

    #inicializar el vector --------------------------------
    MOV     RD, RA
    MOV     RA, RB

    #guardar espacio usado en primera posicion
    STOR    RE, RB      #no hay espacio usado
    
    #guardar tamaño del vector en la segunda posicion
    INC     RB          #RA <- direccion largo vector
    STOR    R1, RB
    INC     RB
    STOR    RD, RB
    DEC     RB
    DEC     RB          #retornar a inicio del vector

    {vec_new_end}
    #terminar funcion
    LOADMEM RB, SP
    JMPR    RB
HLT

#obtiene el valor en el vector v en el indice i
#vector(direccion) en R1, indice en R2
#retorna valor en indice i
#en caso de fallo flag negativo o cero sera verdadero
{vec_get}
    #terminar la funcion si el indice es >= al espacio usado
    LOADMEM RA, R1      #carga el espacio usado del vector en RA
    COMP    RA, R2
    JMPNORZ vec_get_err #si es menor generar error

    INC     R1
    INC     R1          #colocar a R1 en ptr del arreglo
    LOADMEM R1, R1      #R1 <- dir inicio arreglo
    ADD     R1,R2,R1    #sumar el indice a la posicion inicial
    LOADMEM RA, R1      #colocar el valor del indice en RA
    JMP     vec_get_end

    {vec_get_err}
    #causar overflow
    LDINT   RE, 18014398509481984
    {v_g_e}
    JMPOVR  vec_get_end
    SHFTL   RE, RE
    JMP     v_g_e

    {vec_get_end}
    #terminar funcion
    LOADMEM RB, SP
    JMPR    RB
HLT

#coloca el valor n en el vector v en el indice i
#vector(direccion) en R1, indice en R2, dato en R3
#devuelve RA en 0 en caso de fallo, 1 en exito
{vec_set}
    #terminar la funcion si el indice es >= al largo
    LOADMEM RA, R1      #carga espacio usado del vector en RA
    COMP    RA, R2
    JMPNORZ vec_set_err #si es menor genera error

    #colocar valor dentro del arreglo
    #colocar a R1 al inicio del arreglo
    INC     R1
    INC     R1          
    LOADMEM R1, R1

    ADD     R1, R2, R1  #sumar el indice a la posicion inicial
    STOR    R3, R1      #colocar el valor en el arreglo en el indice
    LDINT   RA, 1       #indicar todo fue correcto
    JMP     vec_set_end
    
    {vec_set_err}
    #causar overflow
    LDINT   RE, 18014398509481984
    {v_s_e}
    JMPOVR  vec_set_end
    SHFTL   RE, RE
    JMP     v_s_e
    LDINT   RA, 0       #indicar hubo un fallo

    {vec_set_end}
    #terminar funcion
    LOADMEM RB, SP
    JMPR    RB
HLT

#coloca el valor n al inicio del vector v
#vector(direccion) en R1 y valor en R2
{vec_append}
HLT

{vec_push}
    LOADMEM RA, R1          #cargar espacio usado
    INC     R1
    LOADMEM RB, R1          #cargar largo maximo del vector
    COMP    RA, RB
    JMPNZ vec_push_no_inc   #si no son iguales solo insertar

    #incrementar largo del vector ---------------------------------------------
    #nuevo vector el doble de largo
    SHFTL   RB, RB          #duplicar largo
    STOR    RB, R1          #guardar en vector nuevo largo maximo

    PUSH    R2              #guardar nuevo valor
    PUSH    RA              #guardar espacio usado
    PUSH    R1              #guardar dir ptr arreglo original
    MOV     R1, RB          #pasar nuevo largo como arg


    #llamar malloc --------------------------------------------------
    LDINT   RE, vec_push_return_1
    PUSH    RE
    JMP     malloc          #ir a  malloc
    {vec_push_return_1}

    POP     RE              #sacar dir retorno
    POP     R1              #recobrar dir ptr arreglo del vec original
    MOV     RC, RA          #guardar nuevo ptr de arreglo en RC
    POP     RA              #recobrar espacio usado por el vector
    POP     R2              #recobrar valor a guardar

    JMPOVR  vec_push_end    #si falla malloc terminar

    #preparar registros ---------------------------------------------

    INC     R1
    JMP     vec_push_insert

    #si no se incrementa el largo preparar los registros ----------------------
    {vec_push_no_inc}
    INC     R1
    LOADMEM RC, R1          #en RC debe estar el arreglo de destino

    #insertar nuevo elemento --------------------------------------------------
    {vec_push_insert}

    #copiar datos al nuevo vector -----------------------------------
    LOADMEM RD, R1          #arreglo original en RD para iterar

    PUSH    RC              #guardar arreglo de destino

    #ir al final de los arreglos
    ADD     RD, RA, RD
    DEC     RD              #final es uno menos porque inicia en 0
    ADD     RC, RA, RC
    #no decrementar porque el segundo arreglo es mas largo por 1

    LDINT   RE, 0
    {vec_push_while}
    COMP    RA, RE          #while mientras RE < RA
    JMPNORZ vec_push_while_end

    #pasar valor de arreglo origen a arreglo destino
    LOADMEM RB, RD
    STOR    RB, RC

    #siguiente posicion
    DEC     RC
    DEC     RD
    INC     RE

    JMP     vec_push_while
    {vec_push_while_end}

    #liberar arreglo original si es del caso -----------------------------------
    #obtener direcciones de arreglos origen y destino
    POP     RC
    LOADMEM RD, R1
    
    STOR    R2, RC          #empujar nuevo dato en arreglo destino

    #guardar nuevo espacio usado
    DEC     R1
    DEC     R1
    INC     RA
    STOR    RA, R1

    #si no son iguales liberar arreglo original
    COMP    RC, RD
    JMPZ   vec_push_end

    INC     R1
    INC     R1
    PUSH    R1
    PUSH    RC
    MOV     R1, RD

    LDINT   RE, vec_push_return_2
    PUSH    RE              #direccion de retorno
    JMP     free  #ir a  free
    {vec_push_return_2}
    POP     RE              #sacar dir retorno
    POP     RC              #sacar arreglo nuevo
    POP     R1              #sacar vector

    JMPOVR  vec_push_end    #terminar si fallo free

    STOR    RC, R1          #reemplazar arreglo por nuevo

    {vec_push_end}

    #terminar funcion
    LOADMEM RB, SP
    JMPR    RB
HLT