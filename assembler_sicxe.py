# SIC/XE Assembler with Format 1, 2, 3, and 4 support
import instfile
import re

class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute

symtable = []

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s, t, a):
    symtable.append(Entry(s,t,a))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])
    for i in range(0,instfile.inst_ex.__len__()):
        insert(instfile.inst_ex[i], instfile.inst_token_ex[i], instfile.inst_ex_opcode[i])
    for i in range(0,instfile.dir_ex.__len__()):
        insert(instfile.dir_ex[i], instfile.dir_ex_token[i], instfile.dir_ex_code[i])

file = open('input.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True
defID = False
IdIndex = -1
startAddress = 0
totalSize = 0
pass_num = 1
inst = 0

# Format 4 bits
Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

# Addressing mode bits
Nbitset = 2
Ibitset = 1

# Format 3 bits
Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000

def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '\n':
            startLine = True
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', ',', '@']:
        c = filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # Check if this is a complete C'...' or X'...' literal
        token = filecontent[bufferindex]
        
        if len(token) > 2 and token[0].upper() in ['C', 'X'] and token[1] == "'" and token[-1] == "'":
            # This is a complete literal like C'HELLO' or X'AB'
            
            if token[0].upper() == 'C':
                # C'string' format
                bytestring = token[2:-1]  # Extract content between quotes
                bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
                bytestring = '1_' + bytestring
                p = lookup(bytestring)
                if p == -1:
                    p = insert(bytestring, 'STRING', bytestringvalue)
                tokenval = p
                bufferindex = bufferindex + 1
                return 'STRING'
            else:
                # X'hex' format
                bytestring = token[2:-1]  # Extract hex between quotes
                bytestringvalue = bytestring
                if len(bytestringvalue) % 2 == 1:
                    bytestringvalue = '0' + bytestringvalue
                bytestring = '2_' + bytestring
                p = lookup(bytestring)
                if p == -1:
                    p = insert(bytestring, 'HEX', bytestringvalue)
                tokenval = p
                bufferindex = bufferindex + 1
                return 'HEX'
        
        # Not a literal, process as identifier/keyword
        p=lookup(filecontent[bufferindex].upper())
        if p == -1:
            if defID == True:
                p=insert(filecontent[bufferindex].upper(),'ID',locctr)
            else:
                p=insert(filecontent[bufferindex].upper(),'ID',-1)
        else:
            if (symtable[p].att == -1) and (defID == True):
                symtable[p].att = locctr
        tokenval = p
        bufferindex = bufferindex + 1
        return (symtable[p].token)

def error(s):
    global lineno
    print('line ' + str(lineno) + ': '+s)

def match(token):
    global lookahead
    if lookahead == token:
        old_lookahead = lookahead
        lookahead = lexan()
    else:
        error('Syntax error')

def index():
    global inst, symtable, tokenval
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index register should be X')
        match('REG')
        return True
    return False


## REST FUNCTIONS ##


def Rest1():
    if lookahead in ['F1', 'F2', 'F3', '+']:
        STMT()
    elif lookahead in ['WORD', 'BYTE', 'RESW', 'RESB']:
        Data()


def Rest2():
    global locctr, tokenval
    if lookahead == 'STRING':
        if pass1or2 == 2:
            string_value = symtable[tokenval].att
            string_len = len(string_value) // 2
        string_size = len(symtable[tokenval].att) // 2  
        match('STRING')
        if pass1or2 == 2:
            print("T %06X %02X %s" % (locctr, string_len, string_value))
        locctr += string_size
    elif lookahead == 'HEX':
        if pass1or2 == 2:
            hex_value = symtable[tokenval].att
            hex_len = len(hex_value) // 2
        hex_size = len(symtable[tokenval].att) // 2  
        match('HEX')
        if pass1or2 == 2:
            print("T %06X %02X %s" % (locctr, hex_len, hex_value))
        locctr += hex_size


# rest2 for SIC/XE -> ID INDEX | NUM INDEX | # rest4 | @ rest4 | ε
def rest2_sicxe(is_format4):
    global inst
    
    # if next token starts a new line, no operand
    if lookahead in ['WORD', 'BYTE', 'RESW', 'RESB', 'END', 'EOF']:
        # ε 
        return
    
    # is it a label (new line) or an operand?
    # If ID appears at locctr (being defined now), it's a label, not operand
    if lookahead == 'ID':
        id_att = symtable[tokenval].att
        if id_att == -1 or id_att == locctr:
            # ε
            return
    
    if lookahead == 'ID':  # Simple addressing 
        if pass1or2 == 2:
            inst += symtable[tokenval].att
        match('ID')
        indexed = index()
        if pass1or2 == 2 and indexed:
            if not is_format4:
                inst += Xbit3set
            else:
                inst += Xbit4set
    
    elif lookahead == 'NUM':  # Simple addressing 
        if pass1or2 == 2:
            inst += tokenval
        match('NUM')
        indexed = index()
        if pass1or2 == 2 and indexed:
            if not is_format4:
                inst += Xbit3set
            else:
                inst += Xbit4set
    
    elif lookahead == '#':  # Immediate addressing
        match('#')
        if pass1or2 == 2:
            # Set i bit only (immediate)
            if not is_format4:
                inst = (inst & ~(Nbitset << 16)) | (Ibitset << 16) # It turns off the "n" bit and turns on the "i" bit so the instruction uses immediate addressing
            else:
                inst = (inst & ~(Nbitset << 24)) | (Ibitset << 24)
        Rest4()
    
    elif lookahead == '@':  # Indirect addressing
        match('@')
        if pass1or2 == 2:
            # Set n bit only (indirect)
            if not is_format4:
                inst = (inst & ~(Ibitset << 16)) | (Nbitset << 16) # turns off the "i" bit and turns on the "n" bit 
            else:
                inst = (inst & ~(Ibitset << 24)) | (Nbitset << 24)
        Rest4()


# rest4 -> ID | NUM (for immediate and indirect addressing)
def Rest4():
    global inst, tokenval
    if lookahead == 'ID':
        if pass1or2 == 2:
            inst += symtable[tokenval].att
        match('ID')
    elif lookahead == 'NUM':
        if pass1or2 == 2:
            inst += tokenval
        match('NUM')


def Rest5():
    global inst, tokenval
    if lookahead == ',':
        match(',')
        if pass1or2 == 2:
            inst += symtable[tokenval].att  
        match('REG')


# Format 3/4
def stmt_f3_f4(is_format4):
    global inst, locctr, tokenval
    
    format_size = 4 if is_format4 else 3
    
    if pass1or2 == 2:
        inst = symtable[tokenval].att << (16 if not is_format4 else 24)  # opcode
        # Set n and i bits for simple addressing (both 1)
        if not is_format4:
            if symtable[tokenval].att == 0x4C:  # RSUB special case
                inst += 0  # Set both n and i bits to 0 (NOT SURE)
            else:
                inst += (Nbitset << 16) | (Ibitset << 16)
        else:
            inst += (Nbitset << 24) | (Ibitset << 24)
            inst += Ebit4set  # Set e bit for format 4
    
    if is_format4:
        match('+')
    match('F3')
    locctr += format_size
    
    rest2_sicxe(is_format4)
    
    if pass1or2 == 2:
        if is_format4:
            print("T %06X 04 %08X" % (locctr - 4, inst))
        else:
            print("T %06X 03 %06X" % (locctr - 3, inst))


def STMT():
    global lookahead, inst, locctr, tokenval

    # Format 1
    if lookahead == 'F1':
        if pass1or2 == 2:
            inst = symtable[tokenval].att  
        match('F1')
        locctr += 1
        if pass1or2 == 2:
            print("T %06X 01 %02X" % (locctr - 1, inst))

    # Format 2
    elif lookahead == 'F2':
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8  
        match('F2')
        locctr += 2
    
        # First register
        if pass1or2 == 2:
            inst += (symtable[tokenval].att << 4)  
        reg1 = tokenval
        match('REG')
    
        # rest5: optional second register
        Rest5()
    
        if pass1or2 == 2:
            print("T %06X 02 %04X" % (locctr - 2, inst))

    # Format 3
    elif lookahead == 'F3':
        stmt_f3_f4(False)  

    # Format 4
    elif lookahead == '+':
        stmt_f3_f4(True)  

    else:
        error('Expected instruction')


def Data():
    global locctr, tokenval
    if lookahead == 'WORD':
        match('WORD')
        if pass1or2 == 2:
            word_value = tokenval
        match('NUM')
        if pass1or2 == 2:
            print("T %06X 03 %06X" % (locctr, word_value))
        locctr += 3

    elif lookahead == 'RESW':
        match('RESW')
        resw_count = tokenval
        match('NUM')
        locctr += 3 * resw_count

    elif lookahead == 'RESB':
        match('RESB')
        resb_count = tokenval
        match('NUM')
        locctr += resb_count

    elif lookahead == 'BYTE':
        match('BYTE')
        Rest2()


def Header():
    global lookahead, defID, IdIndex, startAddress, locctr, totalSize, tokenval
    lookahead = lexan()

    defID = True
    IdIndex = tokenval
    match('ID')
    defID = False

    match('START')
    startAddress = locctr = symtable[IdIndex].att = tokenval
    match('NUM')

    if pass1or2 == 2:
        print("H %-6s %06X %06X" % (symtable[IdIndex].string, startAddress, totalSize))


def Body():
    global defID, inst
    defID = True

    if lookahead == 'END':
        return

    if pass1or2 == 2:
        inst = 0

    if lookahead == 'ID':
        if symtable[tokenval].att == -1:
            symtable[tokenval].att = locctr
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

    else:
        if lookahead != 'END' and lookahead != 'EOF':
            print(f"DEBUG: Unexpected lookahead: '{lookahead}', tokenval={tokenval}")
            if lookahead and tokenval < len(symtable):
                print(f"DEBUG: symtable[{tokenval}] = {symtable[tokenval].string}")
            error("Syntax error in Body()")


def Tail():
    global totalSize, startAddress
    match('END')
    match('ID')
    totalSize = locctr - startAddress
    if pass1or2 == 2:
        print("E %06X" % startAddress)

def Parser():
    Header()
    Body()
    Tail()

def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()

    w = file.read()
    
    # Protect C'...' and X'...' literals before splitting
    # Replace them with placeholders that won't be split
    import re as regex_module
    literals = []
    
    def protect_literal(match):
        """Replace literal with placeholder"""
        literals.append(match.group(0))
        return f'__LITERAL_{len(literals)-1}__'
    
    # Protect C'...' and X'...' (case insensitive)
    w_protected = regex_module.sub(r"[CcXx]'[^']*'", protect_literal, w)
    
    filecontent = re.split(r"([\W])", w_protected)
    
    # Restore literals in filecontent
    for i in range(len(filecontent)):
        if filecontent[i].startswith('__LITERAL_'):
            idx = int(filecontent[i].replace('__LITERAL_', '').replace('__', ''))
            filecontent[i] = literals[idx]
    
    # Clean up whitespace
    i=0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != '\n':
        filecontent.append('\n')

    for pass1or2 in range(1,3):
        Parser()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()

main()