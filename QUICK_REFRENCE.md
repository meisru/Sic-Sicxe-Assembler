# SIC/XE Assembler Quick Reference Guide

## 🚀 Quick Start

### For SIC Programs
```bash
python3 Assember_SIC.py
```
Make sure to modify the input file name in the code:
```python
file = open('your_file.sic', 'r')
```

### For SIC/XE Programs
```bash
python3 Assember_SICXE.py
```

---

## 📝 Program Structure

```assembly
LABEL  START  address
       instructions...
LABEL  directives...
       END    LABEL
```

---

## 🔧 SIC Instructions (Format 3 only)

### Data Movement
```assembly
LDA  operand      # Load A
STA  operand      # Store A
LDX  operand      # Load X
STX  operand      # Store X
LDCH operand      # Load character
STCH operand      # Store character
```

### Arithmetic
```assembly
ADD  operand      # A = A + operand
SUB  operand      # A = A - operand
MUL  operand      # A = A * operand
DIV  operand      # A = A / operand
```

### Comparison & Jumping
```assembly
COMP operand      # Compare A with operand
JEQ  operand      # Jump if equal
JGT  operand      # Jump if greater
JLT  operand      # Jump if less
J    operand      # Unconditional jump
JSUB operand      # Jump to subroutine
RSUB              # Return from subroutine
```

### Indexed Addressing
```assembly
LDA  TABLE,X      # A = memory[TABLE + X]
```

---

## 🔧 SIC/XE Additional Instructions

### Format 1 (1 byte, no operands)
```assembly
FIX               # Convert float to integer
FLOAT             # Convert integer to float
HIO               # Halt I/O
SIO               # Start I/O
TIO               # Test I/O
```

### Format 2 (2 bytes, register operands)
```assembly
CLEAR  A          # A = 0
CLEAR  X          # X = 0
COMPR  A,X        # Compare register A with X
TIXR   X          # X = X + 1, compare with A
ADDR   A,X        # A = A + X
SUBR   A,X        # A = A - X
MULR   A,X        # A = A * X
DIVR   A,X        # A = A / X
RMO    A,X        # X = A
SHIFTL A,1        # Shift A left by 1
SHIFTR A,1        # Shift A right by 1
```

### Format 3/4 Addressing Modes

#### Simple Addressing (Direct)
```assembly
LDA  ALPHA        # A = memory[ALPHA]
```

#### Immediate Addressing (#)
```assembly
LDA  #10          # A = 10
LDA  #ALPHA       # A = address of ALPHA
```

#### Indirect Addressing (@)
```assembly
LDA  @PTR         # A = memory[memory[PTR]]
```

#### Indexed Addressing
```assembly
LDA  TABLE,X      # A = memory[TABLE + X]
LDA  #TABLE,X     # Immediate + indexed
LDA  @PTR,X       # Indirect + indexed
```

#### Extended Format (Format 4) - prefix with +
```assembly
+LDA  DATA        # 4-byte instruction, 20-bit address
+JSUB FARAWAY     # Can reach any address in memory
+LDA  #5000       # Immediate with 20-bit value
```

---

## 📦 Assembler Directives

```assembly
START  address    # Program start address
END    label      # Program end, specify entry point

WORD   value      # Reserve 3 bytes, initialize with value
RESW   count      # Reserve count words (3 bytes each)
BYTE   C'text'    # Reserve bytes, initialize with ASCII
BYTE   X'F1'      # Reserve bytes, initialize with hex
RESB   count      # Reserve count bytes
```

---

## 📊 Register Codes (for Format 2)

| Register | Code | Description          |
|----------|------|----------------------|
| A        | 0    | Accumulator          |
| X        | 1    | Index register       |
| L        | 2    | Linkage register     |
| B        | 3    | Base register        |
| S        | 4    | General register     |
| T        | 5    | General register     |
| F        | 6    | Floating-point acc.  |

---

## 📋 Example Programs

### Example 1: Basic SIC
```assembly
COPY   START  0
FIRST  LDA    ALPHA
       STA    BETA
ALPHA  WORD   5
BETA   RESW   1
       END    FIRST
```

### Example 2: SIC with Indexed
```assembly
PROG   START  100
       LDA    TABLE,X
       STA    RESULT
TABLE  WORD   10
RESULT RESW   1
       END    PROG
```

### Example 3: SIC/XE with All Formats
```assembly
TEST   START  0
       CLEAR  A          # Format 2
       LDA    #10        # Format 3, immediate
       +LDA   DATA       # Format 4, extended
       LDA    @PTR       # Format 3, indirect
       FLOAT             # Format 1
DATA   WORD   100
PTR    WORD   DATA
       END    TEST
```

### Example 4: SIC/XE Subroutine
```assembly
MAIN   START  1000
       CLEAR  A
       CLEAR  X
       +JSUB  SUBR       # Format 4 call
       END    MAIN

SUBR   CLEAR  L
       RMO    A,L
       RSUB               # Return
```

---

## 🎯 Object Code Format

### Header Record
```
H<name> <start_addr> <length>
HCOPY   000000 00001E
```

### Text Record
```
T <addr> <len> <object_code>
T 000000 03 00100C
```

### End Record
```
E <start_addr>
E 000000
```

---

## ⚠️ Common Mistakes

1. **Forgetting the label before START**
   ```assembly
   # ❌ Wrong
        START 0
   
   # ✅ Correct
   PROG START 0
   ```

2. **Using undefined symbols**
   ```assembly
   # ❌ Wrong - X not defined
   LDA X
   
   # ✅ Correct
   LDA X
   X WORD 5
   ```

3. **Wrong spacing in directives**
   ```assembly
   # ❌ Wrong - needs proper spacing
   DATAWORD5
   
   # ✅ Correct
   DATA WORD 5
   ```

4. **Mixing SIC and SIC/XE in wrong assembler**
   - Use Assember_SIC.py for pure SIC code
   - Use Assember_SICXE.py for SIC/XE code

---

## 🐛 Debugging Tips

1. **Check line numbers in error messages**
   ```
   line 5: Syntax error
   ```
   Look at line 5 in your source code

2. **Verify forward references are resolved**
   - All symbols should have addresses after pass 1
   - Use labels consistently

3. **Check object code format**
   - Format 3: 6 hex digits (3 bytes)
   - Format 4: 8 hex digits (4 bytes)
   - Format 2: 4 hex digits (2 bytes)
   - Format 1: 2 hex digits (1 byte)

---

## 📚 Additional Resources

- SIC/XE Architecture: Check your textbook for instruction set details
- Opcodes: See instfile.py for complete opcode list
- Test cases: See TEST_CASES.md for comprehensive examples

---

## ✅ Validation Checklist

Before running your program:
- [ ] Program has a label before START
- [ ] All forward references are defined
- [ ] END directive references the correct label
- [ ] Proper spacing between label, mnemonic, and operand
- [ ] Using correct assembler (SIC vs SIC/XE)
- [ ] File name is updated in the assembler code

---

Happy Assembling! 🎉