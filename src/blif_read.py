from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.classicalfunction import classical_function,ClassicalFunction
from qiskit.circuit.classicalfunction.types import Int1
from dd import cudd
from textwrap import dedent
from tweedledum.synthesis import linear_synth
#DCDEBUG
import tracemalloc
import linecache
import os


#from src.circuit_to_logic import *
import logging
import os
import sys
import gc
#import memory-profiler

sys.path.append(os.path.join('../src'))

from circuit_synthesis import iter_to_bool
from calc_cost import all_toffoli,conventional_cost

def blif_read(fpath):
    #tracemalloc.start(10)
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
        if len(line) == 0 or ".end" in line:
            keep_reading = 0
            break
        else:

            qc_args = proc_line(qc_args,line)
    
    if(qc_args["state"] == "func_info"):
        #print("DCDEBUG sizeof node" + str(sys.getsizeof(qc_args["nodes"][-1])))
        #print("DCDEBUG sizeof qc_args" + str(sys.getsizeof(qc_args)))                
        #print("DCDEBUG switch ")
        qc_args["nodes"][-1].synth()
        qc_args["nodes"][-1].synth_cf()

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
        #
        if line.split()[1] == "$false" or line.split()[1] == "$true" or line.split()[1] == "$undef":
            return qc_args
        if (qc_args["state"] != "node_info"):
            if(qc_args["state"] == "func_info"):
                qc_args["nodes"][-1].synth()
                qc_args["nodes"][-1].synth_cf()
                qc_args["nodes"][-1].func = None
                qc_args["nodes"][-1].bdd  = None

                gc.collect()
            qc_args["state"] = "node_info"
            qc_args["nodes"].append(lut_node("node" + str(count),line.split()[1:-1],line.split()[-1]))
            qc_args["count"] += 1
    elif not line[0] == "#" and not '.end' in line:
        if(qc_args["state"] == "node_info"):
            qc_args["state"] = "func_info"
        if(qc_args["state"] == "func_info"):
            qc_args["nodes"][-1].add_sop_expr(line)

    if(qc_args["state"] == "func_info"):
        qc_args["nodes"][-1].synth()
        qc_args["nodes"][-1].synth_cf()

    return qc_args

def comp_methods(fpath):
    qc_args = blif_read(fpath)
    cost    = 0
    cf_cost = 0
    ret_vars = {}
    ret_vars['Circuit'] = fpath.split('/')[-1].split('.')[0]
    for gate in qc_args["nodes"]:
        #gate.synth()
        #gate.synth_cf()
        if gate._fanout in qc_args["outputs"]:
            cost += gate.cost
        else:
            cost += gate.cost * 2
        if gate._fanout in qc_args["outputs"]:
            cf_cost += gate.cf_cost
        else:
            cf_cost += gate.cf_cost * 2
    ret_vars['Proposed'] = cost
    ret_vars['ESOP'] = cf_cost
    return ret_vars

        
class lut_node:
    def __init__(self,name,fanin,fanout):
        self._name   = name
        self._fanin  = [str.replace('$','') for str in fanin]
        self._fanout = fanout
        self.bdd     = cudd.BDD()
        self.cost    = 0
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
        ret_val = self.do_synth(self.func,var_order,qc)
        self.cost = ret_val[1]
        self.qc   = ret_val[0]

    def do_synth(self,func,var_order,qc):
        if func == self.bdd.add_expr('True') or len(var_order) == 1:
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

    def synth_cf(self):
        qc = QuantumCircuit(1)
        self.cf_qc   = ClassicalFunction(dedent(iter_to_bool(self.bdd,self.func))).synth()
        self.cf_cost = conventional_cost(self.cf_qc,[self._fanout])
        self.cf_qc   = None
        gc.collect()

def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))
