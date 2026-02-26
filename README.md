# Emulación de su computador

## Grupo

* Juan David Castañeda Cardenas
* Nicolas Pajaro Sanchez
* Brayan Alejandro Muñoz Perez
* Alvaro Andres Romero Castro
* Nicolas Rodriguez Piraban
*

## Enunciado

1. Implemente, en algún lenguaje de programación de alto nivel, el computador diseñado por Usted
en la Tarea 9.

2. La aplicación debe permitir (de forma simple) escribir directamente sobre los bits de la memoria
RAM (o cargar desde un archivo, es decir debe tenerse implementado el submódulo “Cargador”)
(en cualquier posición o bit) de la máquina propuesta el código binario que se desee (en particular:
Programas en código binario y datos) y, con el programa binario en memoria, debe poder correrse
bien sea paso a paso o bien completo (que ejecute automáticamente todas las instrucciones hasta
encontrar la instrucción de parar).

3. Usar como ejemplos de pruebas al menos los mismos que se usaron en las pruebas de los diseños
de la referida tarea donde se presentan los diseños del computador propuesto.

## TODO list

🧱 A. Definición del modelo (antes de programar)

- Definir tamaño total de la RAM (número de palabras).
- Definir si la RAM es direccionable por byte o por palabra.

Definir número de bits del opcode.

Definir número de bits del operando.

🧠 B. Memoria RAM

- Crear estructura para almacenar la RAM.
- Inicializar RAM en cero.
- Implementar lectura de una palabra de RAM.
- Implementar escritura de una palabra completa en RAM.
- Implementar lectura de un bit específico.
- Implementar escritura de un bit específico.
- Validar direcciones fuera de rango.
- Validar índices de bit fuera de rango.

🧾 C. Registros

Crear registro PC.

Inicializar PC en cero.

Crear registro(s) de propósito general (ej. ACC).

Inicializar registros en cero.

Implementar lectura de registros.

Implementar escritura de registros.

📥 D. Cargador (Loader)

Leer archivo de texto/binario línea por línea.

Convertir cada línea a valor binario interno.

Cargar instrucciones en RAM desde dirección inicial.

Permitir cargar datos (no solo instrucciones).

Detectar overflow de RAM al cargar.

Reiniciar PC después de cargar.

🔄 E. Ciclo de instrucción

Implementar fetch:

Leer instrucción desde RAM[PC].

Incrementar PC.

Implementar decode:

Separar opcode.

Separar operando.

Implementar execute:

Ejecutar instrucción según opcode.

⚙️ F. Implementación de instrucciones (una por una)

(ejemplo genérico, ajusta a tu diseño)

Implementar instrucción LOAD.

Implementar instrucción STORE.

Implementar instrucción ADD.

Implementar instrucción SUB.

Implementar instrucción JMP.

Implementar instrucción JZ / JNZ (si existe).

Implementar instrucción HALT.

Validar operandos de cada instrucción.

Actualizar registros tras cada instrucción.

⏯️ G. Control de ejecución

Implementar ejecución de una sola instrucción.

Detectar instrucción HALT.

Detener ejecución al encontrar HALT.

Evitar ejecución fuera de RAM.

Reiniciar estado de ejecución.

🧪 H. Pruebas internas

Probar lectura/escritura de RAM.

Probar escritura de bits individuales.

Probar carga correcta de programas.

Probar ejecución de una instrucción.

Probar ejecución completa de un programa.

Verificar resultados esperados (Tarea 9).

Probar casos inválidos (direcciones incorrectas).

🧩 I. Integración final

Conectar RAM + registros + CPU.

Verificar coherencia entre módulos.

Ejecutar programas de prueba completos.

Documentar comportamiento esperado.

Congelar versión final del simulador.

🎯 Bonus (opcional, si quieren subir nota)

Reset completo de la máquina.

Volcado de memoria a texto.

Log de ejecución (fetch/decode/execute).

Contador de ciclos.

Soporte para comentarios en archivos de carga.
