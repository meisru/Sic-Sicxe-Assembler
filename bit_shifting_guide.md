# Bit Shifting Guide for New SIC Format

** here claude explains for the quiz question

## Instruction Format (4 bytes / 32 bits)

```
┌─────────┬───┬───┬──────┬──────┬────────────┐
│ opcode  │ n │ i │ 1111 │ REG  │  address   │
│ 6 bits  │ 1 │ 1 │4 bits│4 bits│  16 bits   │
└─────────┴───┴───┴──────┴──────┴────────────┘
```

## Bit Position Mapping

Bits are numbered from **right to left** (0 to 31):

```
Bits 31-26: opcode   (6 bits)
Bit  25:    n        (1 bit)
Bit  24:    i        (1 bit)
Bits 23-20: 1111     (4 bits) - constant marker
Bits 19-16: REG      (4 bits)
Bits 15-0:  address  (16 bits)
```

## How to Calculate Shift Amount

**Rule**: Shift left by the number of bits to the RIGHT of your field.

| Field | Bits to Right | Shift Amount | Code Example |
|-------|---------------|--------------|--------------|
| **address** | 0 | 0 | `address` or `address << 0` |
| **REG** | 16 | 16 | `register << 16` |
| **1111** | 20 | 20 | `0xF << 20` |
| **i bit** | 24 | 24 | `1 << 24` |
| **n bit** | 25 | 25 | `0 << 25` |
| **opcode** | 26 | 26 | `opcode << 26` |

## Building the Instruction

```python
# Start with empty instruction
inst = 0

# Add each field at its position
inst += (opcode << 26)      # Opcode at bits 31-26
inst += (0 << 25)           # n bit at bit 25 (always 0 for this format)
inst += (1 << 24)           # i bit at bit 24 (always 1 for this format)
inst += (0xF << 20)         # "1111" marker at bits 23-20 (always 0xF)
inst += (register << 16)    # Register at bits 19-16
inst += address             # Address at bits 15-0 (no shift needed)
```

## Quick Example

For instruction: `+ LDA X, ALPHA` where LDA=0x00, X=1, ALPHA=0x1000

```python
inst = 0x00 << 26   # 0x00000000  (opcode)
inst += 0 << 25     # 0x00000000  (n bit = 0)
inst += 1 << 24     # 0x01000000  (i bit = 1)
inst += 0xF << 20   # 0x01F00000  (marker = 1111)
inst += 1 << 16     # 0x01F10000  (register X = 1)
inst += 0x1000      # 0x01F11000  (address)

# Result: 0x01F11000
```

## Visual Representation

```
Final instruction: 0x01F11000

Binary breakdown:
0000 0001 1111 0001 0001 0000 0000 0000
│    │    │    │    │                  │
│    │    │    │    └──────────────────┴─ address: 0x1000 (16 bits)
│    │    │    └───────────────────────── REG: 1 (4 bits)
│    │    └────────────────────────────── 1111 marker (4 bits)
│    └─────────────────────────────────── i=1 (1 bit)
└──────────────────────────────────────── n=0, opcode=0x00 (7 bits total)
```

## Fixed vs Variable Values

### Fixed (Constants - same for every instruction):
- `n bit = 0`
- `i bit = 1`
- `"1111" = 0xF`

### Variable (From parsing):
- `opcode` - from symbol table
- `REG` - from register operand
- `address` - from ID operand

## Memory Tip

**Count bits from the right** to find your shift amount:
- address: 0 bits to right → shift 0
- REG: 16 bits to right → shift 16
- 1111: 20 bits to right → shift 20
- i: 24 bits to right → shift 24
- n: 25 bits to right → shift 25
- opcode: 26 bits to right → shift 26

## Code Template

```python
def STMT():
    # ... existing F3 code ...
    
    if lookahead == '+':  # New format indicator
        match('+')
        
        if pass1or2 == 2:
            # Get opcode
            opcode = symtable[tokenval].att
            inst = opcode << 26
            
            # Set fixed bits
            inst += (0 << 25)   # n = 0
            inst += (1 << 24)   # i = 1
            inst += (0xF << 20) # "1111" marker
        
        match('F3')
        
        if pass1or2 == 2:
            # Get register
            register = symtable[tokenval].att
            inst += (register << 16)
        
        match('REG')
        match(',')
        
        if pass1or2 == 2:
            # Get address
            address = symtable[tokenval].att
            inst += address
        
        match('ID')
        
        locctr += 4  # 4 bytes for this format
        
        if pass1or2 == 2:
            print("T %06X 04 %08X" % (locctr - 4, inst))
```