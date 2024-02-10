import pyrtl, sys, io
import generate_ir
from src import alu_decomp_target

if __name__ == "__main__":
    from argparse import ArgumentParser

    # Take in number of pipeline stages as an argument
    parser = ArgumentParser()
    parser.add_argument(
        "-s", "--size", type=int, dest="size", help="size of ALU, as a handwavy measure of complexity (valid values 0--2)"
    )
    args = parser.parse_args()

    alu_size = args.stages if args.stages is not None else 0

    op = pyrtl.Input(bitwidth=4, name="op")
    in1 = pyrtl.Input(bitwidth=32, name="in1")
    in2 = pyrtl.Input(bitwidth=32, name="in2")
    out = pyrtl.Output(bitwidth=32, name="out")

    alu_out = alu_decomp_target(op, in1, in2)

    out <<= alu_out

    pyrtl.synthesize()
    pyrtl.optimize()

    ir = generate_ir.generate_ir(pyrtl.working_block())
    print(ir)
    print("wires: {}, gates: {}".format(
        len(pyrtl.working_block().wirevector_set),
        len(pyrtl.working_block().logic)))
