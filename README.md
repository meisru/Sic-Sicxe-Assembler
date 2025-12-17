# SIC and SIC/XE Assembler - Complete Package ❤️

## 📦 What's Included

This package contains fully functional assemblers for both SIC and SIC/XE architectures, along with comprehensive test cases and documentation.

### Files Provided

#### Assemblers
1. **Assember_SIC.py** - Standard SIC assembler (Format 3 only)
2. **Assember_SICXE.py** - Extended SIC/XE assembler (Formats 1, 2, 3, and 4)
3. **instfile.py** - Instruction definitions and opcodes

#### Test Cases
In the **inputs/** folder

---

## Key Features

### SIC Assembler (Assember_SIC.py)
✅ Format 3 instructions (3 bytes)
✅ Indexed addressing (,X)
✅ Forward reference resolution
✅ Two-pass assembly
✅ Object code generation (H, T, E records)

### SIC/XE Assembler (Assember_SICXE.py)
✅ All SIC features:
✅ Format 1 instructions (1 byte, no operands)
✅ Format 2 instructions (2 bytes, register operands)
✅ Format 3 with immediate (#) and indirect (@) addressing
✅ Format 4 extended instructions 

---

## How to Use

### Step 1: Prepare Your Assembly File
Create a `.sic` file with your assembly code:
```assembly
PROG   START  0
       LDA    VALUE
       STA    RESULT
VALUE  WORD   10
RESULT RESW   1
       END    PROG
```

### Step 2: Modify the Assembler
Open the assembler file and change the input filename:
```python
# Change this line:
file = open('input.sic', 'r')

# To your file:
file = open('your_program.sic', 'r')
```

### Step 3: Run the Assembler
```bash
# For SIC programs:
python3 Assembler_sic.py

# For SIC/XE programs:
python3 Assembler_sicxe.py
```

### Step 4: View the Output
The assembler will output object code in the standard format:
```
HPROG   000000 00000C
T 000000 03 000006
T 000003 03 0C0009
T 000006 03 00000A
E 000000
```

---

I hope it helps you understand SIC/XE architecture better and makes your coursework easier. Good luck with your studies! 