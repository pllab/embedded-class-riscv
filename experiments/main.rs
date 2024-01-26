use std::{io::Read, vec};
use std::collections::HashMap;
use std::fs::*;
use std::io::prelude::*;

#[derive(Clone)]
struct LUT {
    id : usize,
    table: Vec<u8>,
    width: usize,
    inputs: Vec<usize>,
}

impl LUT {
    fn new(line : &str) -> LUT {
        let mut lut = LUT {
            id: 0,
            table: Vec::new(),
            width: 0,
            inputs: Vec::new(),
        };
        for (i, s) in line.split_whitespace().enumerate() {
            if i == 0 {
                lut.id = s.parse::<usize>().unwrap();
            } else if i == 1 {
                lut.width = s.parse::<usize>().unwrap();
                lut.inputs = Vec::new();
                for i in 0..(lut.width as f32).log2().ceil() as usize {
                    lut.inputs.push(i);
                }
            } else {
                lut.table.push(s.parse::<u8>().unwrap());
            }
        }
        // reverse the table
        lut.table.reverse();

        lut
    }

    fn to_circuit(&self) -> Circuit {
        let mut wire_count = self.inputs.len();
        let mut circuit: Circuit = Circuit {
            id: 0,
            inputs: self.inputs.clone(),
            gates: Vec::new(),
        };

        // use the sum of products form
        // https://en.wikipedia.org/wiki/Sum_of_products 

        // for each row in the LUT
        for (i, row) in self.table.iter().enumerate() {
            // if the output is 1
            if *row == 1 {
                // convert the row number to binary
                let mut binary = format!("{:b}", i);
                // pad the binary number with 0s
                while binary.len() < (self.width as f32).log2().ceil() as usize {
                    binary = format!("0{}", binary);
                }

                //construct the input vector for the AND gate
                let mut inputs: Vec<usize> = Vec::new();
                for (j, bit) in binary.chars().enumerate() {
                    if bit == '1' {
                        inputs.push(self.inputs[j]);
                    } else {
                        // add a NOT gate to the circuit
                        circuit.gates.push(LogicGate {
                            gate_type: GateType::NOT,
                            inputs: vec![self.inputs[j]],
                            output: wire_count,
                        });
                        inputs.push(wire_count);
                        wire_count += 1
                    }
                }

                // add an AND gate to the circuit 
                circuit.gates.push(LogicGate {
                    gate_type: GateType::AND,
                    inputs: inputs,
                    output: wire_count,
                });
                wire_count += 1
            }
        }

        // now we OR all of the AND gates together
        // construct the input vector for the OR gate
        let mut inputs: Vec<usize> = Vec::new();
        for gate in &circuit.gates {
            if match gate.gate_type {GateType::AND => true, _ => false} {
                inputs.push(gate.output);
            }
        }
        let OR : LogicGate = LogicGate {
            gate_type: GateType::OR,
            inputs: inputs,
            output: wire_count,
        };

        // add the OR gate to the circuit
        circuit.gates.push(OR);
        circuit.id = self.id;
        circuit
    }
}

#[derive(Clone)]
enum GateType {
    AND,
    OR,
    NOT,
}

#[derive(Clone)]
struct LogicGate {
    gate_type: GateType,
    inputs: Vec<usize>,
    output: usize,
}

#[derive(Clone)]
struct Circuit {
    id: usize,
    inputs: Vec<usize>,
    gates: Vec<LogicGate>
}

impl LogicGate {
    fn new(gate_type: GateType, inputs: Vec<usize>, output: usize) -> LogicGate {
        LogicGate {
            gate_type: gate_type,
            inputs: inputs,
            output: output,
        }
    }

    fn print(&self) {
        match self.gate_type {
            GateType::AND => println!("AND gate: {:?} -> {}", self.inputs, self.output),
            GateType::OR => println!("OR gate: {:?} -> {}", self.inputs, self.output),
            GateType::NOT => println!("NOT gate: {:?} -> {}", self.inputs, self.output),
        }
    }
}

fn get_file_contents(file_name: &str) -> String {
    let file = std::fs::File::open(file_name).unwrap();

    let mut contents = String::new();
    std::io::BufReader::new(file).read_to_string(&mut contents).unwrap();

    contents
}

fn main() {
    let file_name = std::env::args().nth(1).unwrap();
    let contents = get_file_contents(&file_name);
    
    // seperate the last line from the rest of the file
    let mut lines = contents.lines();
    let last_line = lines.nth_back(0).unwrap();
    let contents = lines.collect::<Vec<&str>>().join("\n");


    let mut luts: Vec<LUT> = Vec::new();
    for line in contents.lines() {
        // split each line at the colon and only take the second half
        luts.push(LUT::new(line.split(":").nth(1).unwrap().trim()));
    }

    let mut circuits: Vec<Circuit> = Vec::new();

    for lut in luts.clone() {
        circuits.push(lut.to_circuit());
    }

    // Now we need to connect the circuits together
    // The dependencies of each circuit is given by the first half of each line (before the colon)
    
    // map from circuit ID to circuit
    let mut circuit_map: HashMap<usize, usize> = HashMap::new();
    let mut final_circuit: Circuit = Circuit {
        id: 0,
        inputs: Vec::new(),
        gates: Vec::new(),
    };

    let mut all_circuit_inputs : Vec<Vec<usize>> = Vec::new();

    for line in contents.lines() {
        let string_before_colon = line.split(":").nth(0).unwrap().trim();
        //split the string where there are spaces
        let mut split = string_before_colon.split_whitespace();
        // if there is an I in the string, then we need to add an input

        let mut circuit_inputs = Vec::new();

        // add the dependencies
        for s in split.clone() {
            if s.contains("I"){
                // put the number after the I into the vector if it is not already in there
                let input: u32 = s.chars().nth(1).unwrap().to_digit(10).unwrap();
                if !final_circuit.inputs.contains(&(input as usize)) {
                    final_circuit.inputs.push(input as usize);
                }

                circuit_inputs.push(input as usize);
            } else {
                // the input is the output of another circuit
                let input: u32 = s.chars().nth(1).unwrap().to_digit(10).unwrap();
                circuit_inputs.push(input as usize);

            }
        }

        all_circuit_inputs.push(circuit_inputs);

    }

    let mut current_id: usize = luts.len() + final_circuit.inputs.len();
    // get max between all circuit inputs and circuit ids using max function
    for circuit in circuits.clone() {
        if circuit.id > current_id {
            current_id = circuit.id;
        }
    }

    current_id = if (&current_id > final_circuit.inputs.iter().max().unwrap()) { current_id } else { final_circuit.inputs.iter().max().unwrap().to_owned() } + 1;


    // println!("current id: {}", current_id);
    let mut i: usize = 0;
    for _ in contents.lines() {
        let curr_circuit = circuits[i].clone();
        let associated_inputs = all_circuit_inputs[i].clone();
        // create a hashmap to map from the input of the current circuit to the input of the final circuit
        let mut wire_map: HashMap<usize, usize> = HashMap::new();
        for j in 0..curr_circuit.gates[curr_circuit.gates.len() - 1].output + 1 {
            if curr_circuit.inputs.contains(&j) {
                wire_map.insert(j, associated_inputs[curr_circuit.inputs.iter().position(|&r| r == j).unwrap()]);
            } else if j == curr_circuit.gates[curr_circuit.gates.len() - 1].output {
                wire_map.insert(j, curr_circuit.id);
            } else {
                wire_map.insert(j, current_id);
                current_id += 1;
            }
        }
        // println!("wire map: {:?}", wire_map);
        // now we need to add the gates to the final circuit but replace the inputs with the correct ones from the wire map
        for gate in curr_circuit.gates {
            let mut inputs: Vec<usize> = Vec::new();
            for input in gate.inputs {
                inputs.push(wire_map[&input]);
            }
            final_circuit.gates.push(LogicGate {
                gate_type: gate.gate_type,
                inputs: inputs,
                output: wire_map[&gate.output],
            });
        }
        i += 1;
    }

    // now print out the connected circuit
    println!("Connected circuit:");
    println!("inputs: {:?}", final_circuit.inputs);
    for gate in final_circuit.gates.clone() {
        gate.print();
    }

    // construct the outputs based on the last line of the file
    let outputs : Vec<usize> = last_line.split_whitespace().map(|x| x.parse::<usize>().unwrap()).collect();
    println!("outputs: {:?}", outputs);

    // turn this into a verilog file
    let mut verilog_file = std::fs::File::create("circuit.v").unwrap();
    let mut verilog_string = String::new();
    verilog_string.push_str("module circuit(");
    for i in 0..final_circuit.inputs.len() {
        verilog_string.push_str(&format!("input A{}, ", final_circuit.inputs[i]));
    }
    for i in 0..outputs.len() {
        verilog_string.push_str(&format!("output O{}, ", outputs[i]));
    }
    verilog_string.pop();
    verilog_string.pop();
    verilog_string.push_str(");\n");

    for i in 0..outputs.len() {
        verilog_string.push_str(&format!("wire O{}; \n", outputs[i]));
    }
    for gate in final_circuit.gates.clone() {
        match gate.gate_type {
            GateType::AND => {
                let ins : Vec<String> =  gate.inputs.iter().map(|x| ["A", &x.to_string()].join("").to_string()).collect();
                println!("ins: {}", ins.join(" & "));
                verilog_string.push_str(&format!("wire A{} = {};\n", gate.output, ins.join(" & ")));
            },
            GateType::OR => {
                let ins : Vec<String> =  gate.inputs.iter().map(|x| ["A", &x.to_string()].join("").to_string()).collect();
                println!("ins: {}", ins.join(" | "));
                verilog_string.push_str(&format!("wire A{} = {};\n", gate.output, ins.join(" | ")));
            },
            GateType::NOT => {
                let ins : Vec<String> =  gate.inputs.iter().map(|x| ["A", &x.to_string()].join("").to_string()).collect();
                println!("ins: {}", ins.join(" | "));
                verilog_string.push_str(&format!("wire A{} = ~{};\n", gate.output, ins.join(" | ")));
            },
        }
    }

    for i in 0..outputs.len() {
        verilog_string.push_str(&format!("assign O{} = A{};\n", outputs[i], outputs[i]));
    }
    
    verilog_string.push_str("\nendmodule\n");

    verilog_file.write_all(verilog_string.as_bytes()).unwrap();

}
