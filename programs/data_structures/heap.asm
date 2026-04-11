#este modulo debe ser importado en el proceso de enlazado

#heap de memoria para guardar las estructuras de datos
#la mitad de la memoria para adelante es el heap
#se subdivide el espacio del heap en "paginas"
#al inicio del heap se encuentra un apuntador a la primera pagina vacia
#el primer espacio en la pagina dice si esta ocupado (1)
#el sgundo espacio dice su largo (incluyendo los espacios de informacion)
#si no esta ocupado el tercer espacio apunta a la siguiente pagina vacia

#funcion para reservar memoria (memory allocation)
#recibe un numero de espacios y devuelve una direccion con esa cantidad de espacios
{malloc}
    LDINT   RB, 0x4000       #inicio del heap
    LDINT   RC, 0xE000       #fin del heap

    #revisar que cabe el pedido en el heap
    SUB     RE, RC, RB
    COMP    RE, R1
    JMPNORZ _malloc_sin_espacio

    LOADMEM RD, RB          #obtener apuntado a paginas libres
    LDINT   RE, 0
    COMP    RC, RD          #revisar que esta dentro del heap
    JMPNORZ _malloc_sin_espacio
    COMP    RD, RE          #revisar si esta instanciado
    JMPNZ   _malloc_instanciado

    #NO_instanciado
    MOV     RD, RB

    #esta ocupada la pagina
    INC     RD
    LDINT   RE, 1
    STOR    RE, RD

    #guarda largo de pagina
    INC     RD   
    MOV     R2, R1   
    INC     R2
    INC     R2
    STOR    R2, RD

    #inicializacion siguiente pagina
    INC     RD
    MOV     RA, RD          #guarda direccion de retorno
    ADD     RD, RD, R1      #ir a la siguinte pagina
    STOR    RD, RB          #añadir pagina libre a la lista

    #informacion de ocupado ya es 0

    INC     RD
    SUB     RE, RC, RB      #RE = RC - RB tamaño del heap
    SUB     RE, RE, R2      #restar al tamaño del heap el espacio ocupado
    STOR    RE, RD          #guarda tamaño de pagina

    #el apuntador a la siguiente pagina ya es 0

    JMP     _malloc_end

    {_malloc_next}
    INC     RD
    MOV     RB, RD          #RB es apuntador a actual pagina libre
    LOADMEM RD, RD          #ir a la siguiente posicion
    COMP    RD, RE          #revisa si el apuntador es valido
    JMPNORZ _malloc_sin_espacio

    {_malloc_instanciado}

    INC     RD
    LOADMEM R2, RD          #R2 = largo de pagina
    DEC     R2
    DEC     R2              #quitar los 2 espacios de informacion del largo
    COMP    R2, R1          #revisa largo de pagina
    JMPNORZ _malloc_next

    #la pagina es del largo correcto
    
    #indicar ocupado
    DEC     RD
    LDINT   RE, 1
    STOR    RE, RD
    
    #indicar largo
    INC     RD
    INC     RE
    ADD     RE, R1, RE
    STOR    RE, RD

    #valor de retorno
    INC     RD
    MOV     RA, RD

    #guardar apuntador a siguiente pagina vacia
    LOADMEM RE, RD

    #inicializar sobrante de pagina
    ADD     RD, R1, RD      #ir a la siguiente pagina
    STOR    RD, RB          #cambiar apuntador de antes a nueva pagina
    #ocupado ya esta en 0

    #guardar largo de pagina
    INC     RD
    SUB     R2, R2, R1      #largo sobrante de la pagina
    STOR    R2, RD
    
    #guardar apuntador a siguiente pagina
    INC     RD
    STOR    RE, RD

    JMP     _malloc_end

    {_malloc_sin_espacio}
    #causar overflow
    LDINT   RE, 0x40000000000000    #maximo valor que puede guardar LDINT
    {_malloc_s_e_1}
    JMPOVR  _malloc_end
    SHFTL   RE, RE
    JMP     _malloc_s_e_1
    #retornar direccion nula
    LDINT   RA, 0

    #retornar al procedimiento origen
    {_malloc_end}
    LOADMEM RB, SP
    JMPR    RB
HLT #para marcar fin de la funcion y encontrar la direccion de la siguiente facil

#libera la memoria reservada por malloc
#toma la direccion a liberar en R1
{free}
    #buscar en lista de paginas libres si hay paginas contiguas a esta
    LDINT   RD, 0x4000          #inicio del heap
    {_free_while}
    MOV     RB, RD
    LOADMEM RD, RD
    INC     RD
    LOADMEM RC, RD
    ADD     RC, RD, RC
    INC     RC

    #comparar direccion pagina siguiente a la actual
    COMP    R1, RC
    JMPZ    _free_anterior        #direcciones iguales
    JMPN    _free_no_anterior     #nos pasamos

    INC     RD              #RD = apuntador siguiente pagina libre
    JMP     _free_while

    {_free_no_anterior}
    DEC     RD
    MOV     RC, R1
    DEC     RC
    DEC     RC
    LDINT   RE, 0
    STOR    RE, RC          #ya no esta ocupada la pagina
    STOR    RC, RB          #se coloca la pagina en R1 en la lista
    INC     RC
    LOADMEM RC, RC

    JMP     _free_despues
    {_free_anterior}
    DEC     R1
    LOADMEM RC, R1
    LOADMEM RE, RD
    ADD     RC, RC, RE
    STOR    RC, RD
    INC     RD
    MOV     R1, RD
    LOADMEM RD, RD

    {_free_despues}
    LDINT   RE, 0
    COMP    RD, RE
    JMPZ    _free_end            #terminar si no hay siguiente pagina
 
    #verificar si la siguiente pagina es libre
    ADD     R2, R1, RC
    DEC     R2
    DEC     R2
    COMP    RD, R2
    JMPZ    _free_siguiente

    {_free_no_siguiente}

    STOR    RD, R1          #guardar posicion a siguiente pagina libre
    JMP     _free_end

    {_free_siguiente}
    INC     RD
    LOADMEM RE, RD
    ADD     RC, RC, RE
    DEC     R1              #posicion del largo
    STOR    RC, R1          #guardar largo combinado con la siguiente pagina
    INC     RD
    LOADMEM RE, RD
    INC     R1
    STOR    RE, R1          #guardar posicion de siguiente pagina libre
    
    JMP _free_end

    {_free_fallo}
    #causar overflow
    LDINT   RE, 0x40000000000000    #maximo valor que puede guardar LDINT
    {_free_f_f_1}
    JMPOVR  _free_end
    SHFTL   RE, RE
    JMP     _free_f_f_1

    #retornar al procedimiento origen
    {_free_end}
    LOADMEM RB, SP
    JMPR    RB