import logging
import os
import sys
from dd.autoref import BDD
from dd import cudd
import graphviz
import qiskit.quantum_info as qi #DCDEBUG
import numpy

import pytest
# from mqt.qcec import Configuration, Strategy, verify,Equivalence
from mqt.qcec import Configuration, verify


from qiskit import *
#from qiskit.circuit.classicalfunction import classical_function, Int1



sys.path.append(os.path.join('../src'))
print(sys.path)

from blif_read import proc_line,lut_node,blif_read

class BlifReadTests(object):
    def test_lut_node(self):
        node = lut_node("lut_node")
        print(node._name)
        assert 0 == 1

    def test_proc_line_model(self):
        qc_args = {}
        line    = ".model top"
        bdd     = ""
        qc_args = proc_line(qc_args,line,bdd)
        assert qc_args["model"] == "top"

    def test_proc_line_inputs(self):
        qc_args = {}
        line    = ".inputs totalcoeffs[0] totalcoeffs[1] totalcoeffs[2] totalcoeffs[3] totalcoeffs[4] ctable[0] ctable[1] ctable[2] trailingones[0] trailingones[1]"
        bdd     = ""
        qc_args = proc_line(qc_args,line,bdd)
        assert qc_args["inputs"] == ["totalcoeffs[0]", "totalcoeffs[1]", "totalcoeffs[2]", "totalcoeffs[3]", "totalcoeffs[4]", "ctable[0]", "ctable[1]", "ctable[2]", "trailingones[0]", "trailingones[1]"]

    def test_proc_line_outputs(self):
        qc_args = {}
        line    = ".outputs coeff_token[0] coeff_token[1] coeff_token[2] coeff_token[3] coeff_token[4] coeff_token[5] ctoken_len[0] ctoken_len[1] ctoken_len[2] ctoken_len[3] ctoken_len[4]"
        bdd     = ""
        qc_args = proc_line(qc_args,line,bdd)
        assert qc_args["outputs"] == ["coeff_token[0]", "coeff_token[1]", "coeff_token[2]", "coeff_token[3]", "coeff_token[4]", "coeff_token[5]", "ctoken_len[0]", "ctoken_len[1]", "ctoken_len[2]", "ctoken_len[3]", "ctoken_len[4]"]
        
    def test_proc_line_names(self):
        qc_args = {"state" : "header","count" : 0,"nodes" : {}}
        line    = ".names totalcoeffs[4] totalcoeffs[2] totalcoeffs[3] totalcoeffs[0] ctable[2] totalcoeffs[1] $abc$26552$new_new_n23__"
        bdd     = ""
        qc_args = proc_line(qc_args,line)
        assert qc_args["nodes"]["node0"]._name  == "node0"
        assert qc_args["nodes"]["node0"]._fanin == ["totalcoeffs[4]", "totalcoeffs[2]", "totalcoeffs[3]", "totalcoeffs[0]", "ctable[2]", "totalcoeffs[1]"]
        assert qc_args["nodes"]["node0"]._fanout == "$abc$26552$new_new_n23__"

    def test_str_to_bdd(self):
        line     = "000000 1"
        bdd      = cudd.BDD()
        test_lut = lut_node("",["totalcoeffs[1]", "totalcoeffs[2]", "trailingones[0]", "trailingones[1]", "totalcoeffs[0]", "totalcoeffs[3]"],"$abc$26552$new_new_n23__")

        act_exp = test_lut.str_to_bdd(line,test_lut.fanin,test_lut.bdd)

        assert test_lut.bdd.add_expr("~totalcoeffs[1] & ~totalcoeffs[2] & ~trailingones[0] & ~trailingones[1] & ~totalcoeffs[0] & ~totalcoeffs[3]") == act_exp

    def test_proc_line_func(self):
        qc_args = {"state" : "header","count" : 0,"nodes" : []}
        #model top
        line    = ".model top"
        qc_args = proc_line(qc_args,line)

        #inputs
        line    = ".inputs totalcoeffs[0] totalcoeffs[1] totalcoeffs[2] totalcoeffs[3] totalcoeffs[4] ctable[0] ctable[1] ctable[2] trailingones[0] trailingones[1]"
        qc_args = proc_line(qc_args,line)
        
        line    = ".outputs coeff_token[0] coeff_token[1] coeff_token[2] coeff_token[3] coeff_token[4] coeff_token[5] ctoken_len[0] ctoken_len[1] ctoken_len[2] ctoken_len[3] ctoken_len[4]"
        qc_args = proc_line(qc_args,line)

        line    = ".names totalcoeffs[4] totalcoeffs[2] totalcoeffs[3] totalcoeffs[0] ctable[2] totalcoeffs[1] $abc$26552$new_new_n23__"
        qc_args = proc_line(qc_args,line)
        
        line    = "000000 1"
        qc_args = proc_line(qc_args,line)

        line    = "000001 1"
        qc_args = proc_line(qc_args,line)
        
        assert qc_args["state"] == "func_info"
        assert qc_args["nodes"][-1].bdd.add_expr("~totalcoeffs[4] & ~totalcoeffs[2] & ~totalcoeffs[3] & ~totalcoeffs[0] & ~ctable[2]") == qc_args["nodes"][-1].func

    def test_blif_read(self):
        qc_args = blif_read('/home/dclarino/share/size/cavlc_size_2022.blif')
        assert 1 == 0

    def test_lut_node_synth(self):
        test_lut = lut_node("test",["x3","x1","x2"],"f")
        test_lut.func = test_lut.bdd.add_expr("(x3 & x1 & x2) | (~x3 & ~(~x1 & ~x2))")
        print("DCDEBUG " + str(list(test_lut.bdd.pick_iter(test_lut.func))))
        test_lut.synth()
        assert test_lut.cost == 16
