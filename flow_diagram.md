# Function Flow Diagram - SIC/XE Assembler

## 📊 Complete Function Call Flow

```
main()
  │
  ├─→ init()                    # Initialize symbol table
  │
  └─→ parse() [Pass 1 & 2]
       │
       ├─→ header()             # Process START directive
       │    └─→ lexan() → match('ID') → match('START') → match('NUM')
       │
       ├─→ body()               # Process program body
       │    │
       │    ├─→ [If lookahead == 'ID']
       │    │    └─→ match('ID') → rest1()
       │    │
       │    ├─→ [If lookahead in ['F1','F2','F3','+']]
       │    │    └─→ stmt()
       │    │
       │    └─→ [If lookahead in ['WORD','BYTE','RESW','RESB']]
       │         └─→ data()
       │
       └─→ tail()               # Process END directive
            └─→ match('END') → match('ID')
```

---

## 🔧 Detailed stmt() Branch

```
stmt()
  │
  ├─→ [If lookahead == 'F1']
  │    └─→ stmt_f1()
  │         ├─→ match('F1')
  │         └─→ Output: 1-byte instruction
  │
  ├─→ [If lookahead == 'F2']
  │    └─→ stmt_f2()
  │         ├─→ match('F2')
  │         ├─→ match('REG')
  │         ├─→ rest5()                    # Optional: ,REG
  │         │    └─→ [If ','] match(',') → match('REG')
  │         └─→ Output: 2-byte instruction
  │
  ├─→ [If lookahead == '+']
  │    └─→ stmt_f3_f4(is_format4=True)
  │         ├─→ match('+')
  │         ├─→ match('F3')
  │         ├─→ rest2_sicxe(is_format4=True)    ← NEW FUNCTION
  │         └─→ Output: 4-byte instruction
  │
  └─→ [If lookahead == 'F3']
       └─→ stmt_f3_f4(is_format4=False)
            ├─→ match('F3')
            ├─→ rest2_sicxe(is_format4=False)   ← NEW FUNCTION
            └─→ Output: 3-byte instruction
```

---

## 🎯 rest2_sicxe() Detailed Flow

```
rest2_sicxe(is_format4)
  │
  ├─→ [If lookahead == '#']        IMMEDIATE ADDRESSING
  │    ├─→ match('#')
  │    ├─→ Set i bit only (n=0, i=1)
  │    └─→ rest4()                      ← NEW FUNCTION
  │         │
  │         ├─→ [If 'ID'] match('ID')   # LDA #ALPHA
  │         └─→ [If 'NUM'] match('NUM') # LDA #10
  │
  ├─→ [If lookahead == '@']        INDIRECT ADDRESSING
  │    ├─→ match('@')
  │    ├─→ Set n bit only (n=1, i=0)
  │    └─→ rest4()                      ← NEW FUNCTION
  │         │
  │         ├─→ [If 'ID'] match('ID')   # LDA @PTR
  │         └─→ [If 'NUM'] match('NUM') # LDA @100
  │
  ├─→ [If lookahead == 'ID']       SIMPLE ADDRESSING
  │    ├─→ match('ID')
  │    ├─→ index()                      # Check for ,X
  │    │    └─→ [If ','] match(',') → match('REG')
  │    └─→ [If indexed] Set x bit
  │
  ├─→ [If lookahead == 'NUM']      DIRECT ADDRESS
  │    ├─→ match('NUM')
  │    ├─→ index()                      # Check for ,X
  │    │    └─→ [If ','] match(',') → match('REG')
  │    └─→ [If indexed] Set x bit
  │
  └─→ [Otherwise]                  EPSILON (No operand)
       └─→ Do nothing               # RSUB
```

---

## 📦 data() Branch

```
data()
  │
  ├─→ [If lookahead == 'WORD']
  │    ├─→ match('WORD')
  │    ├─→ match('NUM')
  │    └─→ Output: 3-byte word value
  │
  ├─→ [If lookahead == 'RESW']
  │    ├─→ match('RESW')
  │    ├─→ match('NUM')
  │    └─→ Reserve: count × 3 bytes
  │
  ├─→ [If lookahead == 'RESB']
  │    ├─→ match('RESB')
  │    ├─→ match('NUM')
  │    └─→ Reserve: count bytes
  │
  └─→ [If lookahead == 'BYTE']
       ├─→ match('BYTE')
       └─→ rest2()                      ← DIFFERENT rest2!
            │
            ├─→ [If 'STRING']
            │    ├─→ match('STRING')    # C'HELLO'
            │    └─→ Output: ASCII bytes
            │
            └─→ [If 'HEX']
                 ├─→ match('HEX')       # X'F1'
                 └─→ Output: Hex bytes
```

---

## 🔄 Complete Example Trace

### Assembly Code:
```assembly
PROG   START  0
       LDA    #10
       STA    RESULT
MSG    BYTE   C'HI'
RESULT RESW   1
       END    PROG
```

### Function Call Trace:

```
main()
└─→ parse()
    │
    ├─→ header()
    │   ├─→ lexan() → 'ID' (PROG)
    │   ├─→ match('ID')
    │   ├─→ lexan() → 'START'
    │   ├─→ match('START')
    │   ├─→ lexan() → 'NUM' (0)
    │   └─→ match('NUM')
    │
    ├─→ body() [First call]
    │   ├─→ lookahead = 'F3' (LDA)
    │   ├─→ stmt()
    │   │   └─→ stmt_f3_f4(False)
    │   │       ├─→ match('F3')           # LDA
    │   │       └─→ rest2_sicxe(False)
    │   │           ├─→ lookahead = '#'
    │   │           ├─→ match('#')
    │   │           └─→ rest4()
    │   │               ├─→ lookahead = 'NUM' (10)
    │   │               └─→ match('NUM')
    │   │
    │   └─→ body() [Recursive call]
    │       ├─→ lookahead = 'F3' (STA)
    │       ├─→ stmt()
    │       │   └─→ stmt_f3_f4(False)
    │       │       ├─→ match('F3')       # STA
    │       │       └─→ rest2_sicxe(False)
    │       │           ├─→ lookahead = 'ID' (RESULT)
    │       │           ├─→ match('ID')
    │       │           └─→ index() → False
    │       │
    │       └─→ body() [Recursive call]
    │           ├─→ lookahead = 'ID' (MSG)
    │           ├─→ match('ID')
    │           ├─→ rest1()
    │           │   └─→ data()
    │           │       ├─→ lookahead = 'BYTE'
    │           │       ├─→ match('BYTE')
    │           │       └─→ rest2()       ← DIFFERENT rest2!
    │           │           ├─→ lookahead = 'STRING'
    │           │           └─→ match('STRING')
    │           │
    │           └─→ body() [Recursive call]
    │               ├─→ lookahead = 'ID' (RESULT)
    │               ├─→ match('ID')
    │               └─→ rest1()
    │                   └─→ data()
    │                       ├─→ lookahead = 'RESW'
    │                       ├─→ match('RESW')
    │                       └─→ match('NUM')
    │
    └─→ tail()
        ├─→ match('END')
        └─→ match('ID')
```

---

## 📋 Function Summary Table

| Function | Purpose | Called By | Calls |
|----------|---------|-----------|-------|
| `main()` | Entry point | - | `init()`, `parse()` |
| `init()` | Initialize symbol table | `main()` | `insert()` |
| `parse()` | Two-pass assembly | `main()` | `header()`, `body()`, `tail()` |
| `header()` | Process START | `parse()` | `lexan()`, `match()` |
| `body()` | Process statements | `parse()`, itself (recursive) | `stmt()`, `data()`, `rest1()` |
| `tail()` | Process END | `parse()` | `match()` |
| `stmt()` | Dispatch instructions | `body()` | `stmt_f1()`, `stmt_f2()`, `stmt_f3_f4()` |
| `stmt_f1()` | Format 1 instructions | `stmt()` | `match()` |
| `stmt_f2()` | Format 2 instructions | `stmt()` | `match()`, `rest5()` |
| `stmt_f3_f4()` | Format 3/4 instructions | `stmt()` | `match()`, `rest2_sicxe()` |
| `rest2_sicxe()` | **Handle F3/F4 operands** | `stmt_f3_f4()` | `match()`, `rest4()`, `index()` |
| `rest4()` | **Handle # or @ operand** | `rest2_sicxe()` | `match()` |
| `rest5()` | Optional 2nd register | `stmt_f2()` | `match()` |
| `data()` | Process directives | `body()` | `match()`, `rest2()` |
| `rest2()` | **Handle BYTE data** | `data()` | `match()` |
| `rest1()` | Dispatch after label | `body()` | `stmt()`, `data()` |
| `index()` | Check for ,X | `rest2_sicxe()` | `match()` |
| `match()` | Consume token | Everyone | `lexan()` |
| `lexan()` | Get next token | `match()` | `lookup()`, `insert()` |

---

## 🎨 Key Differences: The Two rest2 Functions

```
╔══════════════════════════════════════════════════════════════╗
║                    rest2() vs rest2_sicxe()                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  rest2()                     rest2_sicxe()                   ║
║  └─ For BYTE directive       └─ For Format 3/4 operands     ║
║      │                           │                           ║
║      ├─ STRING (C'...')          ├─ # rest4 (immediate)     ║
║      │   Example: C'HELLO'       │   Example: #10           ║
║      │                           │                           ║
║      └─ HEX (X'...')             ├─ @ rest4 (indirect)      ║
║          Example: X'F1'          │   Example: @PTR          ║
║                                  │                           ║
║                                  ├─ ID INDEX (simple)        ║
║                                  │   Example: ALPHA,X        ║
║                                  │                           ║
║                                  ├─ NUM INDEX (direct)       ║
║                                  │   Example: 100,X          ║
║                                  │                           ║
║                                  └─ ε (no operand)           ║
║                                      Example: RSUB           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## ✅ Benefits of This Structure

1. **Clear Separation**: Data handling vs instruction handling
2. **Follows Grammar**: Matches the grammar specification exactly
3. **Modular**: Easy to modify individual functions
4. **Reusable**: `rest4()` used by both immediate and indirect
5. **Maintainable**: Each function has a single, clear purpose
6. **Testable**: Can test each function independently

---

This structure makes the assembler easier to understand, debug, and extend! 🎉