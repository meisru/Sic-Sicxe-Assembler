# SIC and SIC/XE Assembler Test Cases

## Test Setup
This document contains test cases for both SIC and SIC/XE assemblers with expected outputs.

---

## SIC TEST CASES

### Test 1: Basic SIC Instructions (test_sic_basic.sic)
**Input:**
```
copy start 0
first  lda alpha
       sta beta
       ldch gamma
alpha  word 10
beta   resw 1
gamma  byte C'A'
       end first
```

**Expected Output:**
- Header: COPY starts at 0x000000
- LDA ALPHA: opcode 0x00, address of alpha
- STA BETA: opcode 0x0C, address of beta
- LDCH GAMMA: opcode 0x50, address of gamma
- WORD 10: value 0x00000A
- RESW 1: reserves 3 bytes (no output)
- BYTE C'A': ASCII value 0x41

---

### Test 2: Indexed Addressing (test_sic_indexed.sic)
**Input:**
```
index start 100
      lda table,x
      sta result
loop  ldch buffer,x
      stch output,x
table word 5
result resw 1
buffer byte C'HELLO'
output resb 5
      end index
```

**Expected Output:**
- Start address: 0x000064 (100 decimal)
- LDA TABLE,X: X bit should be set (0x8000 | address)
- LDCH BUFFER,X: X bit set
- STCH OUTPUT,X: X bit set

---

### Test 3: Forward References (test_sic_forward.sic)
**Input:**
```
prog start 0
     lda x
     sta y
     lda z
x    word 5
y    resw 1
z    word 10
     end prog
```

**Expected Output:**
- All forward references should be resolved correctly
- X at address 0x000009
- Y at address 0x00000C
- Z at address 0x00000F

---

## SIC/XE TEST CASES

### Test 4: Format 1 and Format 2 (test_sicxe_f1f2.sic)
**Input:**
```
test start 0
     fix
     float
     clear a
     clear x
     compr a,x
     tixr x
data word 100
     end test
```

**Expected Output:**
- FIX: 1 byte, opcode 0xC4
- FLOAT: 1 byte, opcode 0xC0
- CLEAR A: 2 bytes, opcode 0xB4, register A=0
- CLEAR X: 2 bytes, opcode 0xB4, register X=1
- COMPR A,X: 2 bytes, opcode 0xA0, registers A,X
- TIXR X: 2 bytes, opcode 0xB8, register X

---

### Test 5: Immediate and Indirect Addressing (test_sicxe_immediate.sic)
**Input:**
```
prog start 0
     lda #10
     lda #value
     lda @ptr
     sta result
value word 100
ptr   word value
result resw 1
      end prog
```

**Expected Output:**
- LDA #10: Immediate mode, i bit set, value 10
- LDA #VALUE: Immediate mode, i bit set, address of value
- LDA @PTR: Indirect mode, n bit set, address of ptr
- STA RESULT: Simple addressing, n and i bits both set

---

### Test 6: Format 4 Extended (test_sicxe_format4.sic)
**Input:**
```
large start 0
      +lda data
      +sta result
      +jsub sub
data  word 5000
result resw 1
sub   +lda #0
      rsub
      end large
```

**Expected Output:**
- +LDA DATA: 4 bytes, e bit set (0x100000), address of data
- +STA RESULT: 4 bytes, e bit set
- +JSUB SUB: 4 bytes, e bit set
- +LDA #0: 4 bytes, e and i bits set, value 0
- RSUB: 3 bytes, no operand

---

### Test 7: Mixed SIC/XE Features (test_sicxe_mixed.sic)
**Input:**
```
mixed start 1000
      clear a
      clear x
      lda #3
      sta length
      +lda #table
loop  ldch @ptr
      stch buffer,x
      tixr x
      compr x,a
      +jsub done
table byte C'TEST'
length resw 1
ptr   word table
buffer resb 10
done  rsub
      end mixed
```

**Expected Output:**
Combines all features:
- Format 2 instructions (CLEAR, TIXR, COMPR)
- Format 3 with immediate (#3)
- Format 4 with immediate (+LDA #TABLE)
- Format 3 with indirect (@PTR)
- Format 3 with indexed (BUFFER,X)
- Format 4 jump (+JSUB)
- Format 3 return (RSUB)

---

## Running the Tests

To run each test:
```bash
# For SIC tests, use Assember.py
# For SIC/XE tests, use Assember_SICXE.py

# Modify the file name in the assembler:
# Change: file = open('input.sic', 'r')
# To: file = open('test_name.sic', 'r')

python3 Assember.py        # For SIC
python3 Assember_SICXE.py  # For SIC/XE
```

---

## Object Code Format

### Header Record
Format: `H<name> <start_address> <program_length>`
- Name: 6 characters, left-justified
- Start address: 6 hex digits
- Program length: 6 hex digits

### Text Record
Format: `T <start_address> <length> <object_code>`
- Start address: 6 hex digits
- Length: 2 hex digits (bytes)
- Object code: Hex digits for instruction/data

### End Record
Format: `E <first_executable_address>`
- First executable address: 6 hex digits

---

## Instruction Formats

### SIC Format 3 (3 bytes)
```
+---+---+---+---+---+---+---+---+
| opcode (8 bits)  |x|  address  |
+---+---+---+---+---+---+---+---+
                   ↑  (15 bits)
                   x bit for indexed
```

### SIC/XE Format 1 (1 byte)
```
+---+---+---+---+---+---+---+---+
|      opcode (8 bits)          |
+---+---+---+---+---+---+---+---+
```

### SIC/XE Format 2 (2 bytes)
```
+---+---+---+---+---+---+---+---+
| opcode (8 bits) | r1  |  r2   |
+---+---+---+---+---+---+---+---+
                  (4 bits)(4 bits)
```

### SIC/XE Format 3 (3 bytes)
```
+---+---+---+---+---+---+---+---+
| opcode (6) |n|i|x|b|p|e|disp  |
+---+---+---+---+---+---+---+---+
              ↑ ↑ ↑ ↑ ↑ ↑  (12 bits)
              addressing flags
```

### SIC/XE Format 4 (4 bytes)
```
+---+---+---+---+---+---+---+---+
| opcode (6) |n|i|x|b|p|e|address|
+---+---+---+---+---+---+---+---+
              ↑ ↑ ↑ ↑ ↑ 1  (20 bits)
              e bit must be 1
```

### Addressing Mode Bits (n, i)
- n=1, i=1: Simple addressing (direct)
- n=0, i=1: Immediate addressing (#)
- n=1, i=0: Indirect addressing (@)
- n=0, i=0: SIC compatible

---

## Register Codes
- A (Accumulator): 0
- X (Index): 1
- L (Linkage): 2
- B (Base): 3
- S (General): 4
- T (General): 5
- F (Floating-point): 6