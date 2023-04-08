from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.classicalfunction import classical_function,ClassicalFunction
from qiskit.circuit.classicalfunction.types import Int1
from dd import cudd
from textwrap import dedent
from tweedledum.synthesis import linear_synth

#from src.circuit_to_logic import *
import logging
import os
import sys
sys.path.append(os.path.join('../src'))

def blif_read(fpath):
    file1 = open(fpath, 'r')
    keep_reading = 1
    count = 0
    qc_args              = { "state" : "header" }
    qc_args["inputs"]    = []
    qc_args["outputs"]   = []
    qc_args["nodes"]     = []
    qc_args["rev_nodes"] = []
    qc_args["count"]     = 0
    while keep_reading:
        line = file1.readline()
        if len(line) == 0:
            keep_reading = 0
            break
        else:
            qc_args = proc_line(qc_args,line)
    

    return qc_args

def proc_line(qc_args,line):
    count = qc_args["count"]
    if line == '\n':
        return qc_args
    if line.split()[0] == '.model':
        qc_args["model"] = line.split()[1]
    elif line.split()[0] == '.inputs':
        qc_args["inputs"] = line.split()[1:]
    elif line.split()[0] == '.outputs':
        qc_args["outputs"] = line.split()[1:]
    elif line.split()[0] == '.names':
        if line.split()[1] == "$false" or line.split()[1] == "$true" or line.split()[1] == "$undef":
            return qc_args
        if (qc_args["state"] != "node_info"):
            qc_args["state"] = "node_info"
            qc_args["nodes"].append(lut_node("node" + str(count),line.split()[1:-1],line.split()[-1]))
            qc_args["count"] += 1
    elif not line[0] == "#":
        if(qc_args["state"] == "node_info"):
            qc_args["state"] = "func_info"
        if(qc_args["state"] == "func_info"):
            qc_args["nodes"][-1].add_sop_expr(line)
    return qc_args

        
class lut_node:
    def __init__(self,name,fanin,fanout):
        self._name   = name
        self._fanin  = [str.replace('$','') for str in fanin]
        self._fanout = fanout
        self.bdd     = cudd.BDD()
        for inp in self._fanin:
            self.bdd.declare(inp)

        self.func    = self.bdd.add_expr('False')

    def add_sop_expr(self,line):
        sop_expr  = self.str_to_bdd(line,self._fanin,self.bdd)
        self.func = self.func | sop_expr

    def str_to_bdd(self,line,bdd_vars,bdd):
        line_arr = line.split()
        count    = 0
        expr_str = ""
        for kbit in line_arr[0]:
            if count > 0:
                expr_str += " & "
            if kbit == "1":
                expr_str += bdd_vars[count]
            else:
                expr_str += "~" + bdd_vars[count]
            count += 1
        return bdd.add_expr(expr_str)

    def synth(self):
        qc = QuantumCircuit(1)
        var_order = self._fanin
        print("DCDEBUG " + str(var_order))
        ret_val = self.do_synth(self.func,var_order,qc)
        self.cost = ret_val[1]
        self.qc   = ret_val[0]

    def do_synth(self,func,var_order,qc):
        #if len(func) == 1 or len(var_order) == 1:
        if func == self.bdd.add_expr('True') or len(var_order) == 1:
            #return CNOT
            return [qc, 0]
        else:
            synth_func0 = self.bdd.let({var_order[0]:False},func)
            ret_arr = [qc,0]
            if synth_func0 == self.bdd.add_expr('True'):
                ret_arr = [qc,ret_arr[1]]
            elif synth_func0 != self.bdd.add_expr('False'):
                synth0 = self.do_synth(synth_func0,var_order[1:],qc)
                ret_arr = [qc,ret_arr[1] + synth0[1] + 4]
            synth_func1 = self.bdd.let({var_order[0]:True},func)
            if synth_func1 == self.bdd.add_expr('True'):
                ret_arr = [qc,ret_arr[1]]
            elif synth_func1 != self.bdd.add_expr('False'):
                synth1 = self.do_synth(synth_func1,var_order[1:],qc)
                ret_arr = [qc,ret_arr[1] + synth1[1] + 4]


            return ret_arr
