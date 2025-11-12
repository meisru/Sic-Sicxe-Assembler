# to debug, add a breakpoint after init() line 194
# then evaluate expression, she clicked something in debug mode
# in expression field she wrote symtable
# then it showed different values from 0 t0 73 or more if extensions were added

import instfile
import re


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []

# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))


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
    # in case of extension of the architecture
    for i in range(0,instfile.inst_ex.__len__()):
        insert(instfile.inst_ex[i], instfile.inst_token_ex[i], instfile.inst_ex_opcode[i])
    for i in range(0,instfile.dir_ex.__len__()):
        insert(instfile.dir_ex[i], instfile.dir_ex_token[i], instfile.dir_ex_code[i])


file = open('input.sic', 'r')  #open the user input file (here called input.sic)
filecontent = []                # the input file will be parsed to
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

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

Nbitset = 2
Ibitset = 1

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


# takes from input file line by line
def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', ',', '@']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex+1] == '\''):
            bytestring = ''
            bufferindex += 2
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '1_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex] == '\''): # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '1_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex+1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue)%2 == 1:
                bytestringvalue = '0'+ bytestringvalue
            bytestring = '2_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue)  # should we deal with literals?
            tokenval = p
        else:
            p=lookup(filecontent[bufferindex].upper())
            if p == -1:
                if defID == True:
                    p=insert(filecontent[bufferindex].upper(),'ID',locctr) # should we deal with case-sensitive?
                else:
                    p=insert(filecontent[bufferindex].upper(),'ID',-1) #forward reference
            else:
                if (symtable[p].att == -1) and (defID == True):
                    symtable[p].att = locctr
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return (symtable[p].token)


def error(s):
    global lineno
    print('line ' + str(lineno) + ': '+s)


def match(token):
    global lookahead
    if lookahead == token:
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


def Rest1():
    if lookahead == 'F3':
        STMT()
    elif lookahead in ['WORD', 'BYTE', 'RESW', 'RESB']:
        Data()


def Rest2():
    global locctr, tokenval
    if lookahead == 'STRING':
        if pass1or2 == 2:
            string_value = symtable[tokenval].att
            string_len = len(string_value) // 2  
        match('STRING')
        if pass1or2 == 2:
            print("T %06X %02X %s" % (locctr, string_len, string_value))
        locctr += (symtable[tokenval].att).__len__() // 2
    elif lookahead == 'HEX':
        if pass1or2 == 2:
            hex_value = symtable[tokenval].att
            hex_len = len(hex_value) // 2  
        match('HEX')
        if pass1or2 == 2:
            print("T %06X %02X %s" % (locctr, hex_len, hex_value))
        locctr += (symtable[tokenval].att).__len__() // 2


# see slide 26 - ch2
def STMT():
    global inst, locctr, tokenval
    if pass1or2 == 2:
        inst = symtable[tokenval].att << 16  
    match('F3')
    locctr += 3  
    if pass1or2 == 2:
        inst += symtable[tokenval].att  
    match('ID')
    indexed = index()
    if pass1or2 == 2:
        if indexed:
            inst += Xbit3set  # set X bit
        print("T %06X 03 %06X" % (locctr - 3, inst))


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


# header -> ID START NUM 
# see slide 26 - ch2
def Header():
    global lookahead, defID, IdIndex, startAddress, locctr, totalSize, tokenval
    lookahead = lexan()

    defID = True
    IdIndex = tokenval  # Save the ID index BEFORE match consumes it
    match('ID')
    defID = False

    match('START')
    startAddress = locctr = symtable[IdIndex].att = tokenval  # tokenval now contains the NUM value
    match('NUM')

    if pass1or2 == 2:
        print("H%-6s %06X %06X" % (symtable[IdIndex].string, startAddress, totalSize))


# for body, two cases: with label or without label, or epsilon
def Body():
    global defID, inst
    defID = True

    if lookahead == 'END':  
        return

    if pass1or2 == 2:
        inst = 0

    if lookahead == 'ID':  # with label
        if symtable[tokenval].att == -1:
            symtable[tokenval].att = locctr
        match('ID')
        defID = False
        Rest1()
        Body()

    elif lookahead == 'F3':  # an instruction without a label
        defID = False  # no label being defined
        if pass1or2 == 2:
            inst = 0
        STMT()
        Body()

    # I removed this line because it's not included in the grammar, this case is for handling data directives without labels
    # elif lookahead in ['WORD', 'BYTE', 'RESW', 'RESB']:  # data without label
    #     defID = False  # no label being defined
    #     Data()
    #     Body()

    else:
        # If none match and it’s not END, it's a syntax issue
        if lookahead != 'END' and lookahead != 'EOF':
            error("Syntax error in Body()")
            

# tail -> END ID
def Tail():
    global totalSize, startAddress
    match('END')
    match('ID')
    totalSize = locctr - startAddress
    if pass1or2 == 2:
        print("E %06X" % startAddress)


# parser SIC 
def parse():
    Header()
    Body()
    Tail()


# def print_symtable():
#     print("\n=== SYMBOL TABLE ===")
#     print("{:<10} {:<10} {:<10}".format("String", "Token", "Attribute"))
#     print("-" * 32)
#     for entry in symtable:
#         print("{:<10} {:<10} {:<10}".format(entry.string, entry.token, str(entry.att)))


def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()

    w = file.read()
    filecontent= re.split(r"([\W])", w)
    i=0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != '\n': # to be sure that the content ends with new line
        filecontent.append('\n')

    for pass1or2 in range(1,3):
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()
    # print_symtable()

main()

    ## add inside main for debugging purpose
    # while True:
    #     lookahead=lexan()
    #     if lookahead == 'EOF':
    #         break
    #     else:
    #         print(lookahead, end=' ')
    # example output: ID START NUM F3 ID F3 ID ID WORD NUM ID RESW NUM END ID
    # ID - "prog" (identifier/label)
    # START - "start" (directive from symbol table)
    # NUM - "0" (number)
    # F3 - "lda" (Format 3 instruction from symbol table)
    # ID - "xx" (identifier/operand)
    # F3 - "sta" (Format 3 instruction)
    # ID - "yy" (identifier/operand)
    # ID - "xx" (identifier/label)
    # WORD - "word" (directive from symbol table)
    # NUM - "5" (number)
    # ID - "yy" (identifier/label)
    # RESW - "resw" (directive from symbol table)
    # NUM - "1" (number)
    # END - "end" (directive from symbol table)
    # ID - "prog" (identifier)