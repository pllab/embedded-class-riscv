import pyrtl

"""
Buffered handshake rules:

1. A data transfer takes place any time (VALID)&&(READY) whether the given
   pipeline stage is ready for it or not.

2. If the output (VALID)&&(!READY) are true, but the input (VALID)&&(READY) is
   true, the data must be stored into a buffer.

3. If !READY on the input, but READY on the output, then the buffer’s values can
   be released and sent forwards, then set READY for the incoming data.

"""

def set_r_valid(i_valid, i_ready, o_ready, o_valid, r_valid_current ):
    r_valid = pyrtl.WireVector(1)
    with pyrtl.conditional_assignment:
        with i_ready:
            r_valid |= 0
        with ~o_valid:
            r_valid |= 0
        with i_valid & o_ready:
            r_valid |= i_valid & o_valid
        with pyrtl.otherwise:
            r_valid |= r_valid_current

    return r_valid

def set_o_valid(i_valid, i_ready, o_valid_current, r_valid ):
    o_valid = pyrtl.WireVector(1)
    with pyrtl.conditional_assignment:
        with i_ready:
            with ~r_valid:
                o_valid |= i_valid
            with pyrtl.otherwise:
                o_valid |= 1
        with ~o_valid:
            o_valid |= i_valid
        with pyrtl.otherwise:
            o_valid |= o_valid_current

    return o_valid

def set_o_ready(i_valid, i_ready, o_ready_current, o_valid):
    o_ready = pyrtl.WireVector(1)
    with pyrtl.conditional_assignment:
        with i_ready:
            o_ready |= 1
        with ~o_valid:
            o_ready |= 1
        with i_valid & o_ready:
            o_ready |= i_valid & o_valid
        with pyrtl.otherwise:
            o_ready |= o_ready_current

    return o_ready

def set_o_data(i_ready, i_data, o_valid, o_data_current, r_valid, r_data):
    o_data = pyrtl.WireVector(W)
    with pyrtl.conditional_assignment:
        with i_ready:
            with ~r_valid:
                o_data |= i_data
            with pyrtl.otherwise:
                o_data |= r_data
        with ~o_valid:
            o_data |= i_data
        with pyrtl.otherwise:
            o_data |= o_data_current

    return o_data

W = 4

stall   = pyrtl.Input(1, 'stall')
out     = pyrtl.Output(W, 'out')

src_valid   = pyrtl.Register(1, 'src_valid', reset_value=1)
src_data    = pyrtl.Register(W, 'src_data', reset_value=1)
# src_buffer  = pyrtl.Register(W, 'src_buffer')

stg1_ready  = pyrtl.Register(1, 'stg1_ready', reset_value=1)
stg1_valid  = pyrtl.Register(1, 'stg1_valid', reset_value=1)
stg1_data   = pyrtl.Register(W, 'stg1_data')
# stg1_buffer = pyrtl.Register(W, 'stg1_buffer')

stg2_ready  = pyrtl.Register(1, 'stg2_ready', reset_value=1)
stg2_valid  = pyrtl.Register(1, 'stg2_valid', reset_value=1)
stg2_data   = pyrtl.Register(W, 'stg2_data')
# stg2_buffer = pyrtl.Register(W, 'stg2_buffer')

sink_ready  = pyrtl.Register(1, 'sink_ready', reset_value=1)
sink_data  = pyrtl.Register(W, 'sink_data')

# Data propagation
src_data.next <<= pyrtl.select(stg1_ready, src_data + 1, src_data)
stg1_data.next <<= pyrtl.select(src_valid & stg1_ready, src_data, stg1_data)
stg2_data.next <<= pyrtl.select(stg1_valid & stg2_ready, stg1_data, stg2_data)
with pyrtl.conditional_assignment:
    # Input valid/ready, but Output valid/!ready
    with (stg1_valid & stg2_ready) & (stg2_valid & ~sink_ready):
        stg2_data.next |= stg2_data
        stg2_buffer.next |= stg1_data
    # Input valid/ready
    with stg1_valid & stg2_ready:
        stg2_data.next |= stg1_data
        stg2_buffer.next |= stg2_buffer
    # Release buffer value
    with ~stg1_ready & stg2_ready:
        stg2_data.next |= stg2_buffer
        stg2_buffer.next |= 0
        

with pyrtl.conditional_assignment:
    with stg2_valid & sink_ready:
        sink_data.next |= stg2_data
# sink_data.next <<= pyrtl.select(stg2_valid & sink_ready, stg2_data, sink_data)

out <<= pyrtl.select(~stall, sink_data, 0)

# Ready signals
sink_ready.next <<= pyrtl.select(stall, 0, 1)
stg2_ready.next <<= pyrtl.select(~sink_ready, 0, 1)
stg1_ready.next <<= pyrtl.select(~stg2_ready, 0, 1)

# Valid signals
src_valid.next <<= 1
stg1_valid.next <<= pyrtl.select(src_valid, 1, 0)
stg2_valid.next <<= pyrtl.select(stg1_valid, 1, 0)

# Test it!
sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

sim_inputs = {
    'stall': '0000100000',
}

sim.step_multiple(sim_inputs)

sim_trace.render_trace(trace_list=['src_data', 'stg1_data', 'stg2_data',\
                                   'sink_data', 'out', 'src_valid',\
                                   'stg1_ready', 'stg1_valid', 'stg2_ready',\
                                   'stg2_valid', 'sink_ready', 'stall'])

# sim_outputs = {
#     'out': '0001234',
# }
#
# sim = pyrtl.Simulation()
#
# sim.step_multiple(sim_inputs, sim_outputs)
#
