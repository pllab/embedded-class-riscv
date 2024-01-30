# Targeted Features for Hardware Decompilation

* Standard Library Components
    - Functions (parameterized, reuse)
    - Loops & Recursion
        + Subcategory: reducers.
* Valid/Ready Handshakes
* *Maybe:* Finite State Machines.
    - State Registers.
* *Maybe:* Nested `with`/`case` expressions.
    - Not particularly fancy, more syntactic, but turning nested MUX's into
      something more readable.

Note: All of the std lib components are "reused" and can be parameterized in
some way, it's just that some of them don't have loops/recursion.

## Standard Library Functions

* `_basic_select`, `[:]` (std lib)
* `_basic_add`, `+` (recursion/loop)
* `_basic_sub`, `-` (recursion/loop)
* `_basic_eq`, `=` (recursion/loop via reducer)
* `_basic_lt`, `<` (recursion/loop)
* `signed_lt` (recursion/loop via `-`)
* `shift_left_logical` (loop via barrel)
* `shift_right_logical` (loop via barrel)
* `shift_right_arithmetic` (loop via barrel)
* `sign_extended`
* `zero_extended`
* `match_bitwidth` (function reuse, std lib) (is that possible?)

## Valid/Ready Handshakes

### Instruction cache (valid/ready)

```
     ---imem.req_valid-->        ---icache.req_valid-->
 CPU <--imem.req_ready--- ICache <--icache.req_ready---  IMem
     ---imem.req_addr--->        ---icache.req_addr--->
     <--imem.resp_data---        <--icache.resp_data---

```

## Finite State Machines

* PC-update state machine.
* Control logic state machine.

## Nested `with` expressions (conditional assignment)

* Control logic.
* Read/write mask logic for data memory load/store.
* ALU op control logic.

# Questions

* Should we make a version using PyRTL modules?
