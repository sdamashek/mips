import struct

def encode_instruction(inst):
    return struct.pack("<I", inst)

def tb(c,length):
    bin_rep = bin(c)[2:].zfill(length)
    return bin_rep[-length:]

def make_r(opcode, rs, rt, rd, shamt, funct):
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

def make_i(opcode, rs, rt, immediate):
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

instructions = b''
instructions += print_string('This string is being printed using a MIPS emulator written in C.\n')
write_code(instructions)
