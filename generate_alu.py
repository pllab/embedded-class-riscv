import pyrtl, sys, io
from .src import alu_decomp_small, alu_decomp_large

def alu_small_builder():
    op = pyrtl.Input(bitwidth=5, name="op")
    in1 = pyrtl.Input(bitwidth=8, name="in1")
    in2 = pyrtl.Input(bitwidth=8, name="in2")
    out = pyrtl.Output(bitwidth=8, name="out")
    alu_out = alu_decomp_small(op, in1, in2)
    out <<= alu_out

def alu32_builder():
    op = pyrtl.Input(bitwidth=5, name="op")
    in1 = pyrtl.Input(bitwidth=32, name="in1")
    in2 = pyrtl.Input(bitwidth=32, name="in2")
    out = pyrtl.Output(bitwidth=32, name="out")
    alu_out = alu_decomp_large(op, in1, in2, 32)
    out <<= alu_out

if __name__ == "__main__":
    from argparse import ArgumentParser, BooleanOptionalAction

    # Take in number of pipeline stages as an argument
    parser = ArgumentParser()
    parser.add_argument(
        "--size", type=str, dest="size", help="size of ALU, as a handwavy measure of complexity: (s)mall, (m)edium, (l)arge"
    )
    parser.add_argument(
        "--out", type=str, dest="output", help="output format: (v)erilog, (o)yster"
    )
    parser.add_argument(
        "--synth", default=False, action=BooleanOptionalAction, help="run PyRTL synthesize (default: no)"
    )
    parser.add_argument(
        "--opt", default=False, action=BooleanOptionalAction, help="run PyRTL optimize (default: no)"
    )
    args = parser.parse_args()

    alu_size = args.size if args.size is not None else 's'
    alu_output = args.output if args.output is not None else 'v'

    bwidth = 8
    if alu_size == 'm':
        bwidth = 16
    elif alu_size == 'l':
        bwidth = 32

    op = pyrtl.Input(bitwidth=5, name="op")
    in1 = pyrtl.Input(bitwidth=bwidth, name="in1")
    in2 = pyrtl.Input(bitwidth=bwidth, name="in2")
    out = pyrtl.Output(bitwidth=bwidth, name="out")

    if alu_size == 's':
        alu_out = alu_decomp_small(op, in1, in2)
        out <<= alu_out
    elif alu_size in ('m', 'l'):
        alu_out = alu_decomp_large(op, in1, in2, bwidth)
        out <<= alu_out

    if args.synth:
        pyrtl.synthesize()
    if args.opt:
        pyrtl.optimize()

    pyrtl.passes._remove_wire_nets(pyrtl.working_block())
    # pyrtl.passes._remove_slice_nets(pyrtl.working_block())
    pyrtl.passes.constant_propagation(pyrtl.working_block(), True)
    # pyrtl.passes._remove_unlistened_nets(pyrtl.working_block())
    # pyrtl.passes.common_subexp_elimination(pyrtl.working_block())

    if alu_output == 'o':
        import generate_ir
        design_out = generate_ir.generate_ir(pyrtl.working_block())
        print(design_out)
    elif alu_output == 'v':
        with io.StringIO() as vfile:
            pyrtl.output_to_verilog(vfile)
            print(vfile.getvalue())

    print("// wires: {}, gates: {}".format(
        len(pyrtl.working_block().wirevector_set),
        len(pyrtl.working_block().logic)))
