import pyrtl
from enum import IntEnum

class Opcode(IntEnum):
    """These numbers come from Table 24.1 of the RISC-V ISA Manual, Volume 1"""

    LOAD = 0b0000011
    IMM = 0b0010011
    AUIPC = 0b0010111
    STORE = 0b0100011
    REG = 0b0110011
    LUI = 0b0110111
    BRANCH = 0b1100011
    JALR = 0b1100111
    JAL = 0b1101111
    SYSTEM = 0b1110011

class ALUOp(IntEnum):
    AND = 0x0
    SLL = 0x1
    SLT = 0x2
    SLTU = 0x3
    XOR = 0x4
    SRL = 0x5
    OR = 0x6
    ADD = 0x7
    SUB = 0x8
    SRA = 0xD
    IMM = 0xE
    NOP = 0xF
    ROR = 0x10
    ROL = 0x11
    PACK = 0x12
    PACKH = 0x13
    ZIP = 0x14
    UNZIP = 0x15
    REV8 = 0x16
    REVB = 0x17
    XNOR = 0x18
    ANDN = 0x19
    ORN = 0x1A
    CLMUL = 0x1B
    CLMULH = 0x1C
    #CZ = 0x17
    #CPOP = 0x18

class MaskMode(IntEnum):
    BYTE = 0x0
    SHORT = 0x1
    WORD = 0x2

class RegWriteSrc(IntEnum):
    ALU = 0b0
    PC = 0b1

class ImmType(IntEnum):
    R = 0
    I = 1
    S = 2
    B = 3
    U = 4
    J = 5

class JumpTarget(IntEnum):
    IMM = 0
    ALU = 1

def control(op, fn3, fn7):
    imm_type = pyrtl.WireVector(bitwidth=3, name="cont_imm_type")
    jump = pyrtl.WireVector(bitwidth=1, name="cont_jump")
    target = pyrtl.WireVector(bitwidth=1, name="cont_target")
    branch = pyrtl.WireVector(bitwidth=1, name="cont_branch")
    branch_inv = pyrtl.WireVector(bitwidth=1, name="cont_branch_inv")
    reg_write = pyrtl.WireVector(bitwidth=1, name="cont_reg_write")
    reg_write_src = pyrtl.WireVector(bitwidth=1, name="cont_reg_write_src")
    mem_write = pyrtl.WireVector(bitwidth=1, name="cont_mem_write")
    mem_read = pyrtl.WireVector(bitwidth=1, name="cont_mem_read")
    alu_imm = pyrtl.WireVector(bitwidth=1, name="cont_alu_imm")
    alu_pc = pyrtl.WireVector(bitwidth=1, name="cont_alu_pc")
    alu_op = pyrtl.WireVector(bitwidth=4, name="cont_alu_op")
    mask_mode = pyrtl.WireVector(bitwidth=2, name="cont_mask_mode")
    mem_sign_ext = pyrtl.WireVector(bitwidth=1, name="cont_mem_sign_ext")

    # Only used for load/store instructions
    mask_mode <<= fn3[0:2]
    mem_sign_ext <<= ~fn3[2]

    # Only used for branch instructions
    branch_inv <<= fn3[0] ^ fn3[2]

    with pyrtl.conditional_assignment(
        defaults={
            jump: 0,
            target: JumpTarget.IMM,
            branch: 0,
            alu_imm: 0,
            alu_pc: 0,
            alu_op: ALUOp.NOP,
            mem_write: 0,
            mem_read: 0,
            reg_write: 0,
            reg_write_src: RegWriteSrc.ALU,
        }
    ):
        with op == Opcode.REG:
            imm_type |= ImmType.R
            alu_imm |= 0
            alu_op |= pyrtl.mux(
                fn3,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.ADD,
                        0x20: ALUOp.SUB,
                    },
                ),
                # ALUOp.SLL,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SLL,
                        0x05: ALUOp.CLMUL,
                    },
                ),
                ALUOp.SLT,
                # ALUOp.SLTU,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SLTU,
                        0x05: ALUOp.CLMULH,
                    },
                ),
                ALUOp.XOR,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SRL,
                        0x20: ALUOp.SRA,
                    },
                ),
                ALUOp.OR,
                ALUOp.AND,
            )
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.IMM:  # i-type
            imm_type |= ImmType.I
            alu_imm |= 1
            alu_op |= pyrtl.mux(
                fn3,
                ALUOp.ADD,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SLL,
                    },
                ),
                ALUOp.SLT,
                ALUOp.SLTU,
                ALUOp.XOR,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SRL,
                        0x20: ALUOp.SRA,
                    },
                ),
                ALUOp.OR,
                ALUOp.AND,
            )
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.LOAD:  # load
            imm_type |= ImmType.I
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            mem_read |= 1
            reg_write |= 1  # redundant
        with op == Opcode.STORE:  # store
            imm_type |= ImmType.S
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            mem_write |= 1
        with op == Opcode.BRANCH:  # branch
            imm_type |= ImmType.B
            branch |= 1
            target |= JumpTarget.IMM
            alu_imm |= 0
            alu_op |= pyrtl.rtllib.muxes.sparse_mux(
                fn3[1:],
                {
                    0x0: ALUOp.XOR,  # beq/bne
                    0x2: ALUOp.SLT,  # blt/bge
                    0x3: ALUOp.SLTU,  # bltu/bgeu
                },
            )
        with op == Opcode.LUI:
            imm_type |= ImmType.U
            alu_imm |= 1
            alu_op |= ALUOp.IMM  # do nothing to the immediate
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.AUIPC:
            imm_type |= ImmType.U
            alu_imm |= 1
            alu_pc |= 1  # use pc as alu_in1
            alu_op |= ALUOp.ADD
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.JAL:
            imm_type |= ImmType.J
            jump |= 1
            target |= JumpTarget.IMM
            reg_write |= 1
            reg_write_src |= RegWriteSrc.PC
        with op == Opcode.JALR:
            imm_type |= ImmType.I
            jump |= 1
            target |= JumpTarget.ALU
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            reg_write |= 1
            reg_write_src |= RegWriteSrc.PC
        with pyrtl.otherwise:  # invalid inst
            pass

    return (
        imm_type,
        jump,
        target,
        branch,
        branch_inv,
        reg_write,
        reg_write_src,
        mem_write,
        mem_read,
        alu_imm,
        alu_pc,
        alu_op,
        mask_mode,
        mem_sign_ext
    )

def control_zbkb(op, fn3, fn7, imm):
    imm_type = pyrtl.WireVector(bitwidth=3, name="cont_imm_type")
    jump = pyrtl.WireVector(bitwidth=1, name="cont_jump")
    target = pyrtl.WireVector(bitwidth=1, name="cont_target")
    branch = pyrtl.WireVector(bitwidth=1, name="cont_branch")
    branch_inv = pyrtl.WireVector(bitwidth=1, name="cont_branch_inv")
    reg_write = pyrtl.WireVector(bitwidth=1, name="cont_reg_write")
    reg_write_src = pyrtl.WireVector(bitwidth=1, name="cont_reg_write_src")
    mem_write = pyrtl.WireVector(bitwidth=1, name="cont_mem_write")
    mem_read = pyrtl.WireVector(bitwidth=1, name="cont_mem_read")
    alu_imm = pyrtl.WireVector(bitwidth=1, name="cont_alu_imm")
    alu_pc = pyrtl.WireVector(bitwidth=1, name="cont_alu_pc")
    alu_op = pyrtl.WireVector(bitwidth=5, name="cont_alu_op")
    mask_mode = pyrtl.WireVector(bitwidth=2, name="cont_mask_mode")
    mem_sign_ext = pyrtl.WireVector(bitwidth=1, name="cont_mem_sign_ext")

    # Only used for load/store instructions
    mask_mode <<= fn3[0:2]
    mem_sign_ext <<= ~fn3[2]

    # Only used for branch instructions
    branch_inv <<= fn3[0] ^ fn3[2]

    with pyrtl.conditional_assignment(
        defaults={
            jump: 0,
            target: JumpTarget.IMM,
            branch: 0,
            alu_imm: 0,
            alu_pc: 0,
            alu_op: ALUOp.NOP,
            mem_write: 0,
            mem_read: 0,
            reg_write: 0,
            reg_write_src: RegWriteSrc.ALU,
        }
    ):
        with op == Opcode.REG:
            imm_type |= ImmType.R
            alu_imm |= 0
            alu_op |= pyrtl.mux(
                fn3,
                pyrtl.rtllib.muxes.sparse_mux( #0
                    fn7,
                    {
                        0x00: ALUOp.ADD,
                        0x20: ALUOp.SUB,
                    },
                ),
                pyrtl.rtllib.muxes.sparse_mux( #1
                    fn7,
                    {
                        0x00: ALUOp.SLL,
                        0x30: ALUOp.ROL,
                    },
                ),
                ALUOp.SLT,  #2
                ALUOp.SLTU, #3
                pyrtl.rtllib.muxes.sparse_mux( #4
                    fn7,
                    {
                        0x00: ALUOp.XOR,
                        0x04: ALUOp.PACK,
                        0x20: ALUOp.XNOR,
                    },
                ),
                pyrtl.rtllib.muxes.sparse_mux( #5
                    fn7,
                    {
                        0x00: ALUOp.SRL,
                        0x20: ALUOp.SRA,
                        0x30: ALUOp.ROR,
                    },
                ),
                pyrtl.rtllib.muxes.sparse_mux( #6
                    fn7,
                    {
                        0x00: ALUOp.OR,
                        0x20: ALUOp.ORN,
                    },
                ),
                pyrtl.rtllib.muxes.sparse_mux( #7
                    fn7,
                    {
                        0x00: ALUOp.AND,
                        0x04: ALUOp.PACKH,
                        0x20: ALUOp.ANDN,
                    },
                ),
            )
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.IMM:  # i-type
            imm_type |= ImmType.I
            alu_imm |= 1
            alu_op |= pyrtl.mux(
                fn3,
                ALUOp.ADD,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SLL,
                        0x04: ALUOp.ZIP,
                    },
                ),
                ALUOp.SLT,
                ALUOp.SLTU,
                ALUOp.XOR,
                pyrtl.rtllib.muxes.sparse_mux(
                    fn7,
                    {
                        0x00: ALUOp.SRL,
                        0x04: ALUOp.UNZIP,
                        0x20: ALUOp.SRA,
                        0x30: ALUOp.ROR,
                        0x34: pyrtl.rtllib.muxes.sparse_mux(
                            imm,
                            {
                                0x698: ALUOp.REV8,
                                0x687: ALUOp.REVB,
                            },
                        ),
                    },
                ),
                ALUOp.OR,
                ALUOp.AND,
            )
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.LOAD:  # load
            imm_type |= ImmType.I
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            mem_read |= 1
            reg_write |= 1  # redundant
        with op == Opcode.STORE:  # store
            imm_type |= ImmType.S
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            mem_write |= 1
        with op == Opcode.BRANCH:  # branch
            imm_type |= ImmType.B
            branch |= 1
            target |= JumpTarget.IMM
            alu_imm |= 0
            alu_op |= pyrtl.rtllib.muxes.sparse_mux(
                fn3[1:],
                {
                    0x0: ALUOp.XOR,  # beq/bne
                    0x2: ALUOp.SLT,  # blt/bge
                    0x3: ALUOp.SLTU,  # bltu/bgeu
                },
            )
        with op == Opcode.LUI:
            imm_type |= ImmType.U
            alu_imm |= 1
            alu_op |= ALUOp.IMM  # do nothing to the immediate
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.AUIPC:
            imm_type |= ImmType.U
            alu_imm |= 1
            alu_pc |= 1  # use pc as alu_in1
            alu_op |= ALUOp.ADD
            reg_write |= 1
            reg_write_src |= RegWriteSrc.ALU
        with op == Opcode.JAL:
            imm_type |= ImmType.J
            jump |= 1
            target |= JumpTarget.IMM
            reg_write |= 1
            reg_write_src |= RegWriteSrc.PC
        with op == Opcode.JALR:
            imm_type |= ImmType.I
            jump |= 1
            target |= JumpTarget.ALU
            alu_imm |= 1
            alu_op |= ALUOp.ADD
            reg_write |= 1
            reg_write_src |= RegWriteSrc.PC
        with pyrtl.otherwise:  # invalid inst
            pass

    return (
        imm_type,
        jump,
        target,
        branch,
        branch_inv,
        reg_write,
        reg_write_src,
        mem_write,
        mem_read,
        alu_imm,
        alu_pc,
        alu_op,
        mask_mode,
        mem_sign_ext
    )
