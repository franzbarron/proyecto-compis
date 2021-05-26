# Domas

Domas is a programming language developed for the final project of the Compiler Design course. The project comprises two programs, a compiler and a virtual machine, similar to the way Java works.

## Team

- Paola Masiel Rijo Martínez A00823735  
- Juan Francisco Barrón Camacho A00823939

## Requirements

Las siguientes herramientas son necesarias:

- [Python 3.6 o superior](https://www.python.org/downloads/)
- [SLY](https://github.com/dabeaz/sly)

## Running the Compiler

To compile code, run the following command:

```
python domasc.py <path/to/file>
```

If one were to compile code in a file inside the tests folder, for example, one would run:

```
python domasc.py tests/hello.dms
```

On a successful compilation, a new file will be generated on the working directory with a .domas extension. This file contains bytecode that can be executed by the virtual machine. The name of this file is the same as the name of the program in the code. For example, code that begins with the line

```
program Hello;
```

will be compiled into Hello.domas.

## Running the Virtual Machine

To execute the compiled program, simply run the following command:

```
python domasv.py <path/to/domas/file>
```

For example, to execute the compiled result of our hello program, one would run

```
python domasv.py Hello.domas
```

## Running the Lexer

To execute only the lexer, which is located in the lexer_parser folder, you can run the following command:

```
python domas_lexer.py <path/to/file>
```
