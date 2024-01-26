module circuit(input A0, input A1, input A3, output O5, output O2);
wire O5; 
wire O2; 
wire A6 = ~A1;
wire A7 = A0 & A6;
wire A2 = A7;
wire A8 = ~A3;
wire A9 = ~A2;
wire A10 = A8 & A9;
wire A5 = A10;
assign O5 = A5;
assign O2 = A2;

endmodule
