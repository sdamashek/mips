#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/syscall.h>

#define OPCODE_BS   26
#define RS_BS       21
#define RT_BS       16
#define RD_BS       11
#define SHAMT_BS    6

#define SIX_MASK    0x0000003f
#define FIVE_MASK   0x0000001f
#define IMMED_MASK  0x0000ffff
#define ADDR_MASK   0x03ffffff

typedef struct r_instruction {
    int opcode;
    int rs;
    int rt;
    int rd;
    int shamt;
    int funct;
} r_instruction;

typedef struct i_instruction {
    int opcode;
    int rs;
    int rt;
    int immediate;
} i_instruction;

typedef struct j_instruction {
    int opcode;
    int address;
} j_instruction;


unsigned int registers[32];
float fpregisters[32];
unsigned int LO, HI;
unsigned long long result, result2, result3, result4;
float fresult;
int *inst_p;
int *inst_max;
int *inst_base;
int *data;
int *data_max;
int *base;

int opcode(int instruction){
    return (instruction >> OPCODE_BS) & SIX_MASK;
}

int rs(int instruction){
    return (instruction >> RS_BS) & FIVE_MASK;
}

int rt(int instruction){
    return (instruction >> RT_BS) & FIVE_MASK;
}

int rd(int instruction){
    return (instruction >> RD_BS) & FIVE_MASK;
}

int shamt(int instruction){
    return (instruction >> SHAMT_BS) & FIVE_MASK;
}

int funct(int instruction){
    return instruction & SIX_MASK;
}

int immediate(int instruction){
    return instruction & IMMED_MASK;
}

int address(int instruction){
    return instruction & ADDR_MASK;
}

void trap(char arg[]){
    printf("TRAP (%s)\n", arg);
    exit(1);
}

int mask_reg(long long reg){
    return reg & 0xffffffff;
}

int se_16_32(int reg){
    int value = (0x0000ffff & reg);
    int mask = 0x00008000;
    if (mask & reg){
        value += 0xffff0000;
    }
    return value;
}

int se_8_32(int reg){
    int value = (0x000000ff & reg);
    int mask = 0x00000080;
    if (mask & reg){
        value += 0xffffff00;
    }
    return value;
}

void process_r(r_instruction inst){
    // printf("%d %d %d %d %d %d\n", inst.opcode, inst.rs, inst.rt, inst.rd, inst.shamt, inst.funct);
    switch(inst.funct){
        case 0x20: // add
            result = registers[inst.rs] + registers[inst.rt];
            registers[inst.rd] = result;
            break;

        case 0x21: // addu
            result = registers[inst.rs] + registers[inst.rt];
            if (result != mask_reg(result)) trap("addu"); // Trap if overflow
            registers[inst.rd] = result;
            break;

        case 0x22: // sub
            result = registers[inst.rs] - registers[inst.rt];
            registers[inst.rd] = result;
            break;

        case 0x23: // subu
            result = registers[inst.rs] - registers[inst.rt];
            if (result != mask_reg(result)) trap("subu");
            registers[inst.rd] = result;
            break;

        case 0x18: // mult
            result = registers[inst.rs] * registers[inst.rt];
            LO = (result << 32) >> 32;
            HI = result >> 32;
            break;

        case 0x19: // multu            
            result = registers[inst.rs] * registers[inst.rt];
            if (registers[inst.rs] != 0 && result / registers[inst.rs] != registers[inst.rt]) trap("multu");
            LO = (result << 32) >> 32;
            HI = result >> 32;
            break;

        case 0x1a: // div
            result = registers[inst.rs] / registers[inst.rt];
            result2 = registers[inst.rs] % registers[inst.rt];
            LO = result;
            HI = result2;
            break;

        case 0x1b: // divu
            result = registers[inst.rs] / registers[inst.rt];
            result2 = registers[inst.rs] % registers[inst.rt];
            if (result != mask_reg(result) || result2 != mask_reg(result2)) trap("divu");
            LO = result;
            HI = result2;
            break;

        case 0x10: // mfhi
            registers[inst.rd] = HI;
            break;

        case 0x12: // mflo
            registers[inst.rd] = LO;
            break;

        // Control registers not implemented atm

        case 0x24: // and
            registers[inst.rd] = registers[inst.rs] & registers[inst.rt];
            break;

        case 0x25: // or
            registers[inst.rd] = registers[inst.rs] | registers[inst.rt];
            break;

        case 0x26: // xor
            registers[inst.rd] = registers[inst.rs] ^ registers[inst.rt];
            break;

        case 0x27: // nor
            registers[inst.rd] = ~(registers[inst.rs] | registers[inst.rt]);
            break;

        case 0x2a: // slt
            registers[inst.rd] = (registers[inst.rs] < registers[inst.rt]);
            break;

        case 0x0: // sll
            registers[inst.rd] = registers[inst.rt] << inst.shamt;
            break;

        case 0x2: // srl
            registers[inst.rd] = registers[inst.rt] >> inst.shamt;
            break;

        case 0x3: // sra
            registers[inst.rd] = ((signed int) registers[inst.rt]) >> inst.shamt;
            break;

        case 0x4: // sllv
            registers[inst.rd] = registers[inst.rt] << registers[inst.rs];
            break;

        case 0x6: // srlv
            registers[inst.rd] = registers[inst.rt] >> registers[inst.rs];
            break;

        case 0x7: // srav
            registers[inst.rd] = ((signed int) registers[inst.rt]) >> registers[inst.rs];
            break;

        case 0x8: // jr
            inst_p = ((int *) (uintptr_t) registers[inst.rs]) - 4;
            break;

        case 0xb: // syscall
            // printf("syscall, register=%d\n", registers[2]);
            switch(registers[2]){
                case 1:
                    printf("%d", registers[4]); // print integer from a0
                    break;
                // floating point

                case 4:
                    printf("%s", (uintptr_t) (base + registers[4])); // print string at a0
                    break;

                case 5:
                    scanf("%d",registers[2]); // read integer into v0
                    break;

                // floating point

                case 8:
                    fgets((char*) (uintptr_t) registers[4], registers[5], stdin); // Read a1 characters into pointer at a0
                    break;

                case 10:
                    exit(0);
                    break;

                case 11:
                    printf("%c", registers[4]); // Print character at a0
                    break;

                case 12:
                    scanf("%c", registers[2]); // Read character into v0
                    break;

                default:
                    trap("invalid syscall");
            }
            break;
        default:
            trap("invalid instruction");

    }
    return;
}

void process_j(j_instruction inst){
    // printf("%x %d\n", inst.opcode, inst.address);
    switch(inst.opcode){
        case 0x2: // j
            inst_p += inst.address;
            break;

        case 0x3: // jal
            registers[31] = (int) inst_p + 1;
            inst_p += inst.address;
            break;

        default:
            trap("invalid instruction");
    }
    return;
}

void process_i(i_instruction inst){
    // printf("%x %d %d %d\n", inst.opcode, inst.rs, inst.rt, inst.immediate);
    switch(inst.opcode){
        case 0x8: // addi
            result = registers[inst.rs] + inst.immediate;
            if (result != mask_reg(result)) trap("addi");
            registers[inst.rt] = result;
            break;

        case 0x9: // addiu
            result = registers[inst.rs] + inst.immediate;
            registers[inst.rt] = result;
            break;

        case 0x23: // lw
            result = *(int*) (uintptr_t) (registers[inst.rs] + inst.immediate);
            registers[inst.rt] = result;
            break;

        case 0x21: // lh
            result = *(short*) (uintptr_t) (registers[inst.rs] + inst.immediate);
            result = se_16_32(result);
            registers[inst.rt] = result;
            break;

        case 0x25: // lhu
            result = *(short*) (uintptr_t) (registers[inst.rs] + inst.immediate);
            registers[inst.rt] = result;
            break;

        case 0x20: // lb
            result = *(char*) (uintptr_t) (registers[inst.rs] + inst.immediate);
            result = se_8_32(result);
            registers[inst.rt] = result;
            break;

        case 0x24: // lbu
            result = *(char*) (uintptr_t) (registers[inst.rs] + inst.immediate);
            registers[inst.rt] = result;
            break;

        case 0x2b: // sw
            *(int*) (uintptr_t) (registers[inst.rs] + inst.immediate) = registers[inst.rt];
            break;

        case 0x29: // sh
            *(short*) (uintptr_t) (registers[inst.rs] + inst.immediate) = (short) registers[inst.rt];
            break;

        case 0x28: // sb
            *(char*) (uintptr_t) (registers[inst.rs] + inst.immediate) = (char) registers[inst.rt];
            break;

        case 0xf: // lui
            registers[inst.rt] = inst.immediate << 16;
            break;

        case 0xc: // andi
            result = registers[inst.rs] & inst.immediate;
            registers[inst.rt] = result;
            break;

        case 0xd: // ori
            result = registers[inst.rs] | inst.immediate;
            registers[inst.rt] = result;
            break;

        case 0xa: // slti
            registers[inst.rt] = (registers[inst.rs] < inst.immediate);
            break;

        case 0x4: // beq
            if (registers[inst.rs] == registers[inst.rt]) inst_p = inst_p + inst.immediate;
            break;

        case 0x5: // bne
            if (registers[inst.rs] != registers[inst.rt]) inst_p = inst_p + inst.immediate;
            break;
        
        default:
            trap("invalid instruction");
    }
    return;
}

void process_inst(){
    int instruction = *inst_p;
    // printf("Instruction=%d, Opcode=%d\n", instruction, opcode(instruction));
    if (opcode(instruction) == 0){
        // R instruction
        r_instruction inst;
        inst.opcode = opcode(instruction);
        inst.rs = rs(instruction);
        inst.rt = rt(instruction);
        inst.rd = rd(instruction);
        inst.shamt = shamt(instruction);
        inst.funct = funct(instruction);
        process_r(inst);
    }

    else if (opcode(instruction) == 2 || opcode(instruction) == 3){
        // J instruction
        j_instruction inst;
        inst.opcode = opcode(instruction);
        inst.address = address(instruction);
        process_j(inst);
    }

    else{
        // I instruction
        i_instruction inst;
        inst.opcode = opcode(instruction);
        inst.rs = rs(instruction);
        inst.rt = rt(instruction);
        inst.immediate = immediate(instruction);
        process_i(inst);
    }
}

void inst_loop(){
    while(inst_p < inst_max){
        // printf("Executing instruction at %p\n", inst_p);
        process_inst();
        inst_p += 1;
    }
}
int main(int argc, char *argv[]){
    if(sizeof(int) != 4){
        printf("sizeof(int) has to be 4 for this interpreter to work.\n");
        exit(1);
    }

    char* file;

    // Check if file is specified, if so set the file to argv
    if (argc > 1){
        file = argv[1];
    }

    else{
        char code_file[] = "code.bin";
        file = code_file;
    }

    // Initialize registers / memory
    memset(registers, 0, sizeof(registers));
    memset(fpregisters, 0, sizeof(fpregisters));
    LO = 0;
    HI = 0;

    // Open instruction file
    FILE *fp;
    fp = fopen(file, "rb");

    // Check if file opened successfully
    if (fp == NULL){
        printf("Could not open instruction file %s.\n", file);
        exit(1);
    }

    fseek(fp, 0L, SEEK_END);
    int size = ftell(fp);
    fseek(fp, 0L, SEEK_SET);

    if (size % 4 != 0){
        trap("size must be a multiple of 4");
    }
    // printf("Read in %d instructions.\n", size/4);

    int *instruction = malloc(size);
    // printf("Allocated %d bytes at %p.\n", size, instruction);
    fread(instruction, 4, size/4, fp);
    inst_p = instruction;
    inst_max = inst_p + size/4;

    base = instruction;

    data = instruction + 1;
    data_max = inst_max;

    // printf("data=%p, data_max=%p, inst_p = %p, inst_base=%p, inst_max=%p\n", data, data_max, inst_p, inst_base, inst_max);
    inst_loop();

    return 0;
}
