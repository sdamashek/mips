import struct
import sys
import re

TEXT = 1
DATA = 2
REG_MAP = {'zero':0,
            'at':1,
            'v0':2,
            'v1':3,
            'a0':4,
            'a1':5,
            'a2':6,
            'a3':7,
            't0':8,
            't1':9,
            't2':10,
            't3':11,
            't4':12,
            't5':13,
            't6':14,
            't7':15,
            's0':16,
            's1':17,
            's2':18,
            's3':19,
            's4':20,
            's5':21,
            's6':22,
            's7':23,
            't8':24,
            't9':25,
            'k0':26,
            'k1':27,
            'gp':28,
            'sp':29,
            'fp':30,
            'ra':31}

labels = {}
offset = 0
offset_regex = re.compile(r'(\d+)\(([^)]+)\)')

def encode_instruction(inst):
    return struct.pack("<I", inst)

def tb(c,length):
    bin_rep = bin(c)[2:].zfill(length)
    return bin_rep[-length:]

def make_r(opcode, rs, rt, rd, shamt, funct):
    print(opcode,rs,rt,rd,shamt,funct)
    opcode = tb(opcode, 6)
    rs = tb(rs, 5)
    rt = tb(rt, 5)
    rd = tb(rd, 5)
    shamt = tb(shamt, 5)
    funct = tb(funct, 6)
    instruction = opcode + rs + rt + rd + shamt + funct
    print(instruction)
    instruction = int(instruction, 2)
    return encode_instruction(instruction)

def make_j(opcode, address):
    print(opcode, address)
    opcode = tb(opcode, 6)
    address = tb(address, 26)
    instruction = opcode + address
    print(instruction)
    instruction = int(instruction, 2)
    return encode_instruction(instruction)

def make_i(opcode, rs, rt, immediate):
    print(opcode,rs,rt,immediate)
    opcode = tb(opcode, 6)
    rs = tb(rs, 5)
    rt = tb(rt, 5)
    immediate = tb(immediate, 16)
    instruction = opcode + rs + rt + immediate
    print(instruction)
    instruction = int(instruction, 2)
    return encode_instruction(instruction)

def write_code(inst):
    f = open('code.bin','wb')
    f.write(inst)
    f.close()

def print_string(string):
    inst = b''
    inst += make_i(0x9,0,2,11)
    for char in string:
        inst += make_i(0x9,0,4,ord(char))
        inst += make_r(0,0,0,0,0,0xb)
    return inst

def li(reg,imm):
    inst = b''
    inst += make_i(0xf,0,reg,imm&0xffff0000)
    inst += make_i(0xd,reg,reg,imm&0x0000ffff)
    return inst

def la(reg, label):
    inst = b''
    inst += make_i(0xf,0,reg,labels[label.lower()]&0xffff0000)
    inst += make_i(0xd,reg,reg,labels[label.lower()]&0x0000ffff)
    return inst

def syscall():
    return make_r(0,0,0,0,0,0xb)

def do_exit():
    inst = b''
    inst += li(2,10)
    inst += syscall()
    return inst

def error(string):
    print("ERROR: %s" % string)
    sys.exit(1)

def register(reg):
    # Map a named register to a number

    if re.match(r'\$\d+', reg):
        return int(re.match(r'\$(\d+)$', reg).group(1)) # Already a number register

    name = re.match(r'\$([\w\d]+)$', reg)
    if not name:
        error("Register called with non-register %s" % reg)
    name = name.group(1)
    if name not in REG_MAP:
        error("Register %s is an invalid register" % reg)

    return REG_MAP[name]

def parse_offset(offset):
    ret = offset_regex.search(offset)
    if not ret:
        if offset.lower() in labels:
            return (labels[offset.lower()],'$gp')
        error("Invalid memory offset.")
    return (int(ret.groups()[0]),ret.groups()[1])

def tob10(st):
    if st.startswith('0x'):
        return int(st,16)
    return int(st)

def mul(d,s,t):
    inst = b''
    inst += make_r(0,0,s,t,0,0x18)
    inst += make_r(0,d,0,0,0,0x12)
    return inst

def div(d,s,t):
    inst = b''
    inst += make_r(0,0,s,t,0,0x1a)
    inst += make_r(0,d,0,0,0,0x12)
    return inst

def rem(d,s,t):
    inst = b''
    inst += make_r(0,0,s,t,0,0x1a)
    inst += make_r(0,d,0,0,0,0x10)
    return inst

def valid(arr):
    return [x for x in arr if x != None]

def process_inst(inst):
    i = re.search(r'(\w+) ?([\$\w\d\.()]+)?(?: *, *([\$\w\d\.()]+))*$', inst)
    if not i:
        error("Instruction \"%s\" is invalid" % inst)

    i = i.groups()
    name = i[0]
    print(name)
    print(i[1:])

    # R types

    if name == 'add':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x20)

    elif name == 'addu':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x21)

    elif name == 'sub':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x22)

    elif name == 'subu':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x23)

    elif name == 'mult':
        return make_r(0,0,register(i[1]),register(i[2]),0,0x18)

    elif name == 'multu':
        return make_r(0,0,register(i[1]),register(i[2]),0,0x19)

    elif name == 'div':
        return make_r(0,0,register(i[1]),register(i[2]),0,0x1a)

    elif name == 'divu':
        return make_r(0,0,register(i[1]),register(i[2]),0,0x1a)

    elif name == 'mfhi':
        return make_r(0,register(i[1]),0,0,0,0x10)

    elif name == 'mflo':
        return make_r(0,register(i[1]),0,0,0,0x12)

    elif name == 'and':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x24)

    elif name == 'or':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x25)

    elif name == 'xor':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x26)

    elif name == 'nor':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x27)

    elif name == 'slt':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x2a)

    elif name == 'sll':
        return make_r(0,register(i[1]),0,register(i[2]),i[3],0x0)

    elif name == 'srl':
        return make_r(0,register(i[1]),0,register(i[2]),i[3],0x2)

    elif name == 'sra':
        return make_r(0,register(i[1]),0,register(i[2]),i[3],0x3)

    elif name == 'sllv':
        return make_r(0,register(i[1]),register(i[3]),register(i[2]),0x4)

    elif name == 'srlv':
        return make_r(0,register(i[1]),register(i[3]),register(i[2]),0x6)

    elif name == 'srav':
        return make_r(0,register(i[1]),register(i[3]),register(i[2]),0x7)

    elif name == 'jr':
        return make_r(0,0,register(i[1]),0,0x8)

    # I instructions

    elif name == 'addi':
        return make_i(0x8,register(i[2]),register(i[1]),i[3])

    elif name == 'addiu':
        return make_i(0x9,register(i[2]),register(i[1]),i[3])

    elif name == 'lw':
        off = parse_offset(i[2])
        print(off)
        return make_i(0x23,register(off[1]),register(i[1]),off[0])

    elif name == 'lh':
        off = parse_offset(i[2])
        return make_i(0x21,register(off[1]),register(i[1]),off[0])

    elif name == 'lhu':
        off = parse_offset(i[2])
        return make_i(0x25,register(off[1]),register(i[1]),off[0])

    elif name == 'lb':
        off = parse_offset(i[2])
        return make_i(0x20,register(off[1]),register(i[1]),off[0])

    elif name == 'lbu':
        off = parse_offset(i[2])
        return make_i(0x24,register(off[1]),register(i[1]),off[0])

    elif name == 'sw':
        off = parse_offset(i[2])
        return make_i(0x2b,register(off[1]),register(i[1]),off[0])

    elif name == 'sh':
        off = parse_offset(i[2])
        return make_i(0x29,register(off[1]),register(i[1]),off[0])

    elif name == 'sb':
        off = parse_offset(i[2])
        return make_i(0x28,register(off[1]),register(i[1]),off[0])

    elif name == 'lui':
        return make_i(0xf,0,register(i[1]),i[2])

    elif name == 'andi':
        return make_i(0xc,register(i[1]),register(i[2]),i[3])

    elif name == 'ori':
        return make_i(0xd,register(i[1]),register(i[2]),i[3])

    elif name == 'slti':
        return make_i(0xa,register(i[1]),register(i[2]),i[3])

    elif name == 'beq':
        return make_i(0x4,register(i[1]),register(i[2]),i[3])

    elif name == 'bne':
        return make_i(0x5,register(i[1]),register(i[2]),i[3])

    # J instructions

    elif name == 'j':
        return make_j(0x2,i[1])

    elif name == 'jal':
        return make_j(0x3,i[1])

    # Pseudo instructions

    elif name == 'syscall':
        return syscall()

    elif name == 'li':
        return li(register(i[1]),int(i[2]))

    elif name == 'la':
        return la(register(i[1]),i[2])

    elif name == 'move':
        return make_r(0,register(i[2]),0,register(i[1]),0,0x20)

    elif name == 'clear':
        return make_r(0,0,0,register(i[1]),0,0x20)

    elif name == 'not':
        return make_r(0,register(i[2]),0,register(i[1]),0,0x27)

    elif name == 'b':
        return make_i(0x4,0,0,labels[i[1].lower()])

    elif name == 'mul':
        return mul(register(i[1]),register(i[2]),register(i[3]))

    elif name == 'nop':
        return make_r(0,0,0,0,0,0)

    error("Invalid instruction: %s" % i[0])

def main():
    name = 'code.asm'
    if len(sys.argv) > 1:
        name = sys.argv[1]

    assembly = open(name,'r').read()

    section = None
    instructions = assembly.strip().split('\n')
    for i in range(len(instructions)):
        if instructions[i].strip() == '.text':
            for j in range(len(instructions[i+1:])):
                if instructions[j].strip() == '.data':
                    instructions = instructions[j:] + instructions[i:j]
                    break

    output = b''
    text = make_i(0xe,0,0,0)
    data = b''

    ptr = 1
    for arr in range(len(instructions)):
        inst = instructions[arr]
        splinst = instructions[arr].strip()
        if not section:
            if splinst == ".data":
                section = DATA
            elif splinst == ".text":
                section = TEXT
            else:
                error("No section specified")
        elif section == TEXT:
            if splinst == ".data":
                section = DATA
                continue

            elif re.match(r'[\w\d_]+:',splinst):
                labelname = re.match(r'([\w\d_]+):', splinst).group(1)
                if labelname in labels:
                    error("Label %s already defined" % labelname)

                labels[labelname.lower()] = ptr # Integer (4 byte) offset
                text += b'\x00\x00\x00\x00'

            else:
                text += process_inst(splinst)

            ptr += 1

        elif section == DATA:
            if splinst == ".text":
                section = TEXT
                continue

            elif re.match(r'[\w\d_]+: *.+',splinst):
                match = re.match(r'([\w\d_]+): *([\w\.]+) +([\$\w\d\.() \\"]+)(?: *, *([\$\w\d\.() \\"]+))*$',splinst)
                if not match:
                    error("Invalid DATA label: \"%s\"" % splinst)

                labelname = match.group(1)
                typename = match.group(2)
                vals = match.groups()[2:]

            else:
                match = re.match(r'([\w\.]+) +([\$\w\d\.() \\"]+)(?: *, *([\$\w\d\.() \\"]+))*$',splinst)
                if not match:
                    continue

                labelname = None
                typename = match.group(1)
                vals = match.groups()[1:]

            print(labelname,typename,vals)

            if typename == '.asciiz':
                string = re.match(r'"([^"]*)"',vals[0])
                if not string:
                    error("invalid asciiz")
                string = bytes(string.group(1),"utf-8").decode("unicode_escape")
                labels[labelname.lower()] = ptr 
                st = string + "\x00"
                st = st + ("\x00" * (4-(len(st) % 4)))
                print("FINAL: %s" % st)
                ptr += len(st)//4 - 1
                data += bytes(st,"utf-8")

            elif typename == '.ascii':
                string = re.match(r'"([^"]*)"',vals[0])
                if not string:
                    error("invalid ascii")
                string = bytes(string.group(1),"utf-8").decode("unicode_escape")
                labels[labelname.lower()] = ptr 
                st = string
                st = st + ("\x00" * (4-(len(st) % 4)))
                print("FINAL: %s" % st)
                ptr += len(st)//4 - 1
                data += bytes(st,"utf-8")

            elif typename == '.byte':
                arr = valid(re.match(r'([\dx]+)(?: *, *([\dx]+))*$',vals[0]).groups())
                if not arr:
                    error("invalid bytes")
                labels[labelname.lower()] = ptr 
                arr = list(map(tob10, arr))
                st = b''.join([struct.pack("<B",x) for x in arr])
                st += st + (b"\x00" * (4-(len(st) % 4)))
                ptr += len(st)//4 - 1
                data += st

            elif typename == '.halfword':
                arr = valid(re.match(r'([\dx]+)(?: *, *([\dx]+))*$',vals[0]).groups())
                if not arr:
                    error("invalid halfword")
                labels[labelname.lower()] = ptr 
                arr = list(map(tob10, arr))
                st = b''.join([struct.pack("<H",x) for x in arr])
                st += st + (b"\x00" * (4-(len(st) % 4)))
                ptr += len(st)//4 - 1
                data += st

            elif typename == '.word':
                arr = valid(re.match(r'([\dx]+)(?: *, *([\dx]+))*$',vals[0]).groups())
                if not arr:
                    error("invalid word")
                labels[labelname.lower()] = ptr 
                arr = list(map(tob10, arr))
                print(arr)
                st = b''.join([struct.pack("<I",x) for x in arr])
                st += st + (b"\x00" * (4-(len(st) % 4)))
                ptr += len(st)//4 - 1
                data += st

            elif typename == '.space':
                numbytes = int(vals[0])
                st = bytes(numbytes)
                st = st + (b"\x00" * (4-(len(st) % 4)))
                ptr += len(st)//4 - 1
                data += st

            
            ptr += 1

    text += do_exit()

    if 'main' not in labels:
        error("Main label not defined")

    output += make_j(0x2, labels['main'])
    output += data
    output += text

    write_code(output)


if __name__ == '__main__':  main()
