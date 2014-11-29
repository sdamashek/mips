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

def process_inst(inst):
    i = re.search(r'(\w+) ?([\$\w\d\.()]+)?(?: *, *([\$\w\d\.()]+))*$', inst)
    if not i:
        error("Instruction \"%s\" is invalid" % inst)

    i = i.groups()
    name = i[0]
    print(name)
    print(i[1:])

    if name == 'add':
        return make_r(0,register(i[1]),register(i[2]),register(i[3]),0,0x20)

    elif name == 'syscall':
        return syscall()

    elif name == 'li':
        return li(register(i[1]),int(i[2]))

    elif name == 'la':
        return la(register(i[1]),i[2])

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

            
            ptr += 1

    text += do_exit()

    if 'main' not in labels:
        error("Main label not defined")

    output += make_j(0x2, labels['main'])
    output += data
    output += text

    write_code(output)


if __name__ == '__main__':  main()
