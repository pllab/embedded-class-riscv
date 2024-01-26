import pyrtl, sys, io
import generate_ir
from src import rv_cpu

if __name__ == "__main__":
    from argparse import ArgumentParser

    # Take in number of pipeline stages as an argument
    parser = ArgumentParser()
    parser.add_argument(
        "-s", "--stages", type=int, dest="stages", help="number of pipeline stages"
    )
    parser.add_argument(
        "-e", "--ext", type=str, dest="extension", help="ISA extension rv(i), zbk(b), zbk(c)"
    )
    args = parser.parse_args()

    num_stages = args.stages if args.stages is not None else 1
    extension = args.extension if args.extension is not None else 'i'

    rv_cpu(num_stages=num_stages, isa=extension)

    pyrtl.optimize()
    pyrtl.synthesize()
    # pyrtl.optimize()

    ir = generate_ir.generate_ir(pyrtl.working_block())
    print(ir)
    print("wires: {}, gates: {}".format(
        len(pyrtl.working_block().wirevector_set),
        len(pyrtl.working_block().logic)))
