# SIC/XE Assembler with PC-relative, Base-relative, Relocation, and Program Blocks

import instfile
import re

class Entry:
    def __init__(self, string, token, attribute, block=-1):
        self.string = string
        self.token = token
        self.att = attribute
        self.block = block  # Program block: 0=default, 1=CDATA, 2=CBLCK

symtable = []
baseValue = -1          # BASE register value
modArray = []           # Modification records for relocation

def lookup(s):
    for i in range(len(symtable)):
        if s == symtable[i].string: 
            return i
    return -1

def insert(s, t, a, b=-1):
    symtable.append(Entry(s, t, a, b))
    return len(symtable) - 1

def init():
    for i in range(len(instfile.inst)):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(len(instfile.directives)):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])
    # Extensions
    for i in range(len(instfile.inst_ex)):
        insert(instfile.inst_ex[i], instfile.inst_token_ex[i], instfile.inst_ex_opcode[i])
    for i in range(len(instfile.dir_ex)):
        insert(instfile.dir_ex[i], instfile.dir_ex_token[i], instfile.dir_ex_code[i])

file = open('inputs/exam2.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = [0, 0, 0]      # Location counters for 3 blocks
block = 0               # Current block (0, 1, or 2)
lookahead = ''
startLine = True
defID = False
IdIndex = -1
startAddress = 0
totalSize = 0
defaultSize = 0
cdataSize = 0
cblckSize = 0
inst = 0

# Format 4 bit masks
Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

# Format 3 addressing mode bits (n and i at bits 17 and 16)
Nbit3set = 0x20000
Ibit3set = 0x10000

# Format 4 addressing mode bits
Nbit4set = 0x2000000
Ibit4set = 0x1000000

# Format 3 bit masks
Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000

def is_hex(s):
    if len(s) > 2 and s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    return False

def lexan():
    global filecontent, tokenval, lineno, bufferindex, startLine

    while True:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '\n':
            startLine = True
            bufferindex += 1
            lineno += 1
        else:
            break
    
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])
        bufferindex += 1
        return 'NUM'
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)
        bufferindex += 1
        return 'NUM'
    elif filecontent[bufferindex] in ['+', '#', ',', '@']:
        c = filecontent[bufferindex]
        bufferindex += 1
        return c
    else:
        # Handle C'...' and X'...' literals
        token = filecontent[bufferindex]
        
        if len(token) > 2 and token[0].upper() in ['C', 'X'] and token[1] == "'" and token[-1] == "'":
            if token[0].upper() == 'C':
                bytestring = token[2:-1]
                bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
                bytestring = '1_' + bytestring
                p = lookup(bytestring)
                if p == -1:
                    p = insert(bytestring, 'STRING', bytestringvalue)
                tokenval = p
                bufferindex += 1
                return 'STRING'
            else:  # X'...'
                bytestring = token[2:-1]
                bytestringvalue = bytestring
                if len(bytestringvalue) % 2 == 1:
                    bytestringvalue = '0' + bytestringvalue
                bytestring = '2_' + bytestring
                p = lookup(bytestring)
                if p == -1:
                    p = insert(bytestring, 'HEX', bytestringvalue)
                tokenval = p
                bufferindex += 1
                return 'HEX'
        
        # Regular identifier/keyword
        p = lookup(filecontent[bufferindex].upper())
        if p == -1:
            if defID:
                p = insert(filecontent[bufferindex].upper(), 'ID', locctr[block], block)
            else:
                p = insert(filecontent[bufferindex].upper(), 'ID', -1)
        else:
            if symtable[p].att == -1 and defID:
                symtable[p].att = locctr[block]
                symtable[p].block = block
        tokenval = p
        bufferindex += 1
        return symtable[p].token

def error(s):
    global lineno
    print(f'line {lineno}: {s}')

def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')

def index(ext):
    """Check for indexed addressing (,X)"""
    global inst
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index register should be X')
        match('REG')
        return True
    return False

def rest6(ext):
    """Handle operands for immediate (#) and indirect (@) addressing"""
    global inst, baseValue, block, locctr
    
    if lookahead == 'NUM':
        num_val = tokenval
        match('NUM')
        if pass1or2 == 2:
            if ext:  # Format 4
                inst += num_val
            else:  # Format 3
                if -2048 <= num_val <= 2047:
                    inst += num_val
                else:
                    current_pc = get_actual_address(block, locctr[block])
                    disp = num_val - current_pc
                    if -2048 <= disp <= 2047:
                        inst += Pbit3set
                        inst += disp if disp >= 0 else (disp & 0xFFF)
                    else:
                        if baseValue < 0:
                            error(f"Address {num_val:X} out of PC range and BASE not set")
                        else:
                            disp = num_val - baseValue
                            if 0 <= disp <= 4095:
                                inst += Bbit3set
                                inst += disp
                            else:
                                error(f"Address {num_val:X} out of range")
    
    elif lookahead == 'ID':
        target_addr = symtable[tokenval].att
        match('ID')
        if pass1or2 == 2:
            if ext:  # Format 4
                inst += target_addr
                # Add modification record
                actual_addr = get_actual_address(block, locctr[block] - 4)
                modArray.append(actual_addr + 1)
            else:  # Format 3 - PC-relative
                current_pc = get_actual_address(block, locctr[block])
                disp = target_addr - current_pc
                if -2048 <= disp <= 2047:
                    inst += Pbit3set
                    inst += disp if disp >= 0 else (disp & 0xFFF)
                else:
                    if baseValue < 0:
                        error(f"Address {target_addr:X} out of PC range and BASE not set")
                    else:
                        disp = target_addr - baseValue
                        if 0 <= disp <= 4095:
                            inst += Bbit3set
                            inst += disp
                        else:
                            error(f"Address {target_addr:X} out of range")

def rest3(ext):
    """Handle Format 3/4 operands with all addressing modes"""
    global inst, baseValue, block, locctr
    
    if lookahead == 'NUM':  # Simple addressing with number
        num_val = tokenval
        match('NUM')
        indexed = index(ext)
        
        if pass1or2 == 2:
            if ext:  # Format 4
                inst += Nbit4set + Ibit4set
                inst += num_val
                if indexed:
                    inst += Xbit4set
            else:  # Format 3
                inst += Nbit3set + Ibit3set
                if -2048 <= num_val <= 2047:
                    inst += num_val
                else:
                    current_pc = get_actual_address(block, locctr[block])
                    disp = num_val - current_pc
                    if -2048 <= disp <= 2047:
                        inst += Pbit3set
                        inst += disp if disp >= 0 else (disp & 0xFFF)
                    else:
                        if baseValue < 0:
                            error(f"Address {num_val:X} out of PC range and BASE not set")
                        else:
                            disp = num_val - baseValue
                            if 0 <= disp <= 4095:
                                inst += Bbit3set
                                inst += disp
                            else:
                                error(f"Address {num_val:X} out of range")
                if indexed:
                    inst += Xbit3set
    
    elif lookahead == 'ID':  # Simple addressing with symbol
        target_addr = symtable[tokenval].att
        match('ID')
        indexed = index(ext)
        
        if pass1or2 == 2:
            if ext:  # Format 4
                inst += Nbit4set + Ibit4set
                inst += target_addr
                if indexed:
                    inst += Xbit4set
                # Add modification record using actual address
                actual_addr = get_actual_address(block, locctr[block] - 4)
                modArray.append(actual_addr + 1)
            else:  # Format 3 - PC-relative
                inst += Nbit3set + Ibit3set
                current_pc = get_actual_address(block, locctr[block])
                disp = target_addr - current_pc
                if -2048 <= disp <= 2047:
                    inst += Pbit3set
                    inst += disp if disp >= 0 else (disp & 0xFFF)
                else:
                    if baseValue < 0:
                        error(f"Address {target_addr:X} out of PC range and BASE not set")
                    else:
                        disp = target_addr - baseValue
                        if 0 <= disp <= 4095:
                            inst += Bbit3set
                            inst += disp
                        else:
                            error(f"Address {target_addr:X} out of range")
                if indexed:
                    inst += Xbit3set
    
    elif lookahead == '#':  # Immediate addressing
        match('#')
        if pass1or2 == 2:
            inst += Ibit4set if ext else Ibit3set
        rest6(ext)
    
    elif lookahead == '@':  # Indirect addressing
        match('@')
        if pass1or2 == 2:
            inst += Nbit4set if ext else Nbit3set
        rest6(ext)

def rest4(format5):
    """Handle Format 2 second register"""
    global inst
    if lookahead == ',':
        match(',')
        if pass1or2 == 2:
            if format5:
                inst += symtable[tokenval].att << 8
            else:
                inst += symtable[tokenval].att
        match('REG')
        if format5:
            rest4(False)

def get_actual_address(block_num, block_locctr):
    """Calculate actual address accounting for block concatenation"""
    global defaultSize, cdataSize
    if block_num == 0:
        return block_locctr
    elif block_num == 1:
        return block_locctr + defaultSize
    else:  # block_num == 2
        return block_locctr + defaultSize + cdataSize


def STMT():
    """Generate instruction code"""
    global inst, locctr, block, modArray
    
    if lookahead == 'F1':  # Format 1
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        match('F1')
        locctr[block] += 1
        if pass1or2 == 2:
            actual_addr = get_actual_address(block, locctr[block]-1)
            print(f"T {actual_addr:06X} 01 {inst:02X}")
    
    elif lookahead == 'F2':  # Format 2
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8
        match('F2')
        locctr[block] += 2
        if pass1or2 == 2:
            inst += symtable[tokenval].att << 4
        match('REG')
        rest4(False)
        if pass1or2 == 2:
            actual_addr = get_actual_address(block, locctr[block]-2)
            print(f"T {actual_addr:06X} 02 {inst:04X}")
    
    elif lookahead == 'F3':  # Format 3
        instr_index = tokenval
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 16
        match('F3')
        locctr[block] += 3
        # Check if this is RSUB (only F3 instruction with no operand)
        if symtable[instr_index].string == 'RSUB':
            if pass1or2 == 2:
                inst += Nbit3set + Ibit3set
                actual_addr = get_actual_address(block, locctr[block]-3)
                print(f"T {actual_addr:06X} 03 {inst:06X}")
        else:
            rest3(False)
            if pass1or2 == 2:
                actual_addr = get_actual_address(block, locctr[block]-3)
                print(f"T {actual_addr:06X} 03 {inst:06X}")
    
    elif lookahead == '+':  # Format 4
        match('+')
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 24
            inst += Ebit4set
        match('F3')
        locctr[block] += 4
        rest3(True)
        if pass1or2 == 2:
            actual_addr = get_actual_address(block, locctr[block]-4)
            print(f"T {actual_addr:06X} 04 {inst:08X}") 


def Data():
    """Handle data directives"""
    global locctr, tokenval, block
    
    if lookahead == 'WORD':
        match('WORD')
        if pass1or2 == 2:
            word_value = tokenval
        match('NUM')
        if pass1or2 == 2:
            actual_addr = get_actual_address(block, locctr[block])
            print(f"T {actual_addr:06X} 03 {word_value:06X}")
        locctr[block] += 3
    
    elif lookahead == 'RESW':
        match('RESW')
        resw_count = tokenval
        match('NUM')
        locctr[block] += 3 * resw_count
    
    elif lookahead == 'RESB':
        match('RESB')
        resb_count = tokenval
        match('NUM')
        locctr[block] += resb_count
    
    elif lookahead == 'BYTE':
        match('BYTE')
        if lookahead == 'STRING':
            if pass1or2 == 2:
                string_value = symtable[tokenval].att
                string_len = len(string_value) // 2
                actual_addr = get_actual_address(block, locctr[block])
                print(f"T {actual_addr:06X} {string_len:02X} {string_value}")
            string_size = len(symtable[tokenval].att) // 2
            match('STRING')
            locctr[block] += string_size
        elif lookahead == 'HEX':
            if pass1or2 == 2:
                hex_value = symtable[tokenval].att
                hex_len = len(hex_value) // 2
                actual_addr = get_actual_address(block, locctr[block])
                print(f"T {actual_addr:06X} {hex_len:02X} {hex_value}")
            hex_size = len(symtable[tokenval].att) // 2
            match('HEX')
            locctr[block] += hex_size

def Rest1():
    """Dispatch to instruction or data"""
    if lookahead in ['F1', 'F2', 'F3', '+']:
        STMT()
    elif lookahead in ['WORD', 'BYTE', 'RESW', 'RESB']:
        Data()

def rest10():
    """Handle USE directive"""
    global block
    if lookahead == 'CDATA':
        block = 1
        match('CDATA')
    elif lookahead == 'CBLCK':
        block = 2
        match('CBLCK')
    else:
        block = 0

def Header():
    """Process START directive"""
    global lookahead, defID, IdIndex, startAddress, locctr, totalSize, tokenval
    
    lookahead = lexan()
    defID = True
    IdIndex = tokenval
    match('ID')
    defID = False
    
    match('START')
    startAddress = locctr[0] = locctr[1] = locctr[2] = tokenval
    symtable[IdIndex].att = tokenval
    match('NUM')
    
    if pass1or2 == 2:
        print(f"H {symtable[IdIndex].string:<6s} {startAddress:06X} {totalSize:06X}")

def Body():
    """Process program body"""
    global defID, inst, baseValue, block
    
    defID = True
    
    if lookahead == 'END':
        return
    
    if pass1or2 == 2:
        inst = 0
    
    if lookahead == 'ID':
        if symtable[tokenval].att == -1:
            symtable[tokenval].att = locctr[block]
            symtable[tokenval].block = block
        match('ID')
        defID = False
        Rest1()
        Body()
    
    elif lookahead in ['F1', 'F2', 'F3', '+']:
        defID = False
        if pass1or2 == 2:
            inst = 0
        STMT()
        Body()
    
    elif lookahead in ['WORD', 'BYTE', 'RESW', 'RESB']:
        defID = False
        Data()
        Body()
    
    elif lookahead == 'BASE':
        defID = False
        match('BASE')
        if pass1or2 == 2:
            baseValue = symtable[tokenval].att
        match('ID')
        Body()
    
    elif lookahead == 'USE':
        defID = False
        match('USE')
        rest10()
        Body()
    
    else:
        if lookahead != 'END' and lookahead != 'EOF':
            error("Syntax error in Body()")

def Tail():
    """Process END directive"""
    global totalSize, startAddress, defaultSize, cdataSize, cblckSize
    
    match('END')
    end_symbol_index = tokenval  # Save the symbol index
    match('ID')
    
# Calculate sizes - subtract startAddress!
    defaultSize = locctr[0] - startAddress  # Not locctr[0]!
    cdataSize = locctr[1] - startAddress    # Not locctr[1]!
    cblckSize = locctr[2] - startAddress    # Not locctr[2]!
    totalSize = defaultSize + cdataSize + cblckSize
    
    # Adjust symbol addresses based on blocks
    if pass1or2 == 1:
        for i in range(len(symtable)):
            if symtable[i].token == 'ID':
                if symtable[i].block == 1:
                    symtable[i].att += defaultSize
                elif symtable[i].block == 2:
                    symtable[i].att += defaultSize + cdataSize
    
    if pass1or2 == 2:
        # Print modification records
        for addr in modArray:
            print(f"M {addr:06X} 05")
        # Use the END symbol's address, not startAddress
        end_address = symtable[end_symbol_index].att
        print(f"E {end_address:06X}")

def Parser():
    """Main parser"""
    Header()
    Body()
    Tail()

def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno, baseValue, modArray, block
    init()
    
    w = file.read()
    
    # Protect literals
    import re as regex_module
    literals = []
    
    def protect_literal(match):
        literals.append(match.group(0))
        return f'__LITERAL_{len(literals)-1}__'
    
    w_protected = regex_module.sub(r"[CcXx]'[^']*'", protect_literal, w)
    filecontent = re.split(r"([\W])", w_protected)
    
    # Restore literals
    for i in range(len(filecontent)):
        if filecontent[i].startswith('__LITERAL_'):
            idx = int(filecontent[i].replace('__LITERAL_', '').replace('__', ''))
            filecontent[i] = literals[idx]
    
    # Clean whitespace
    i = 0
    while True:
        while i < len(filecontent) and filecontent[i] in [' ', '', '\t']:
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    
    if filecontent[-1] != '\n':
        filecontent.append('\n')
    
    # Two-pass assembly
    for pass1or2 in range(1, 3):
        baseValue = -1
        modArray = []
        block = 0
        Parser()
        bufferindex = 0
        locctr = [0, 0, 0]
        lineno = 1
    
    file.close()

if __name__ == '__main__':
    main()