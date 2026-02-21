# SIC/XE Assembler

## Overview
Two-pass assembler for SIC/XE (Simplified Instructional Computer - Extended) architecture supporting all standard features plus custom extensions.

## Features
- **Two-pass assembly**: Symbol resolution and object code generation
- **Multiple formats**: F1 (1 byte), F2 (2 bytes), F3 (3 bytes), F4 (4 bytes)
- **Addressing modes**: Immediate (#), Indirect (@), Indexed (,X), PC-relative, BASE-relative
- **Program blocks**: USE directive for code blocks (default, CDATA, CBLCK)
- **Relocation**: Modification records for relocatable code

## Usage
```bash
python3 assembler_sicxe.py
```

Input file: `inputs/your_program.sic`

## Input Format
```assembly
PROG    START   0
        LDA     VALUE
        BASE    TABLE
        +LDX    #4096
VALUE   WORD    5
TABLE   RESW    100
        END     PROG
```

## Output
Object code in standard SIC/XE format:
- **H record**: Header (name, start address, length)
- **T records**: Text (object code)
- **M records**: Modification (relocation info)
- **E record**: End (execution start address)

Example output:
```
H PROG   000000 000199
T 000000 03 032006
T 000003 04 05100FA0
T 000007 03 000005
M 000004 05
E 000000
```

This is based on the initial code provided in the course CS423.
