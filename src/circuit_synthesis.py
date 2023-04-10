from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.classicalfunction import classical_function,ClassicalFunction
from qiskit.circuit.classicalfunction.types import Int1
from dd import cudd
from textwrap import dedent
import calc_cost
from tweedledum.synthesis import linear_synth

#from src.circuit_to_logic import *
import logging
import os
import sys
import re
sys.path.append(os.path.join('../src'))
# print(sys.path)

from circuit_to_logic import *

def calculate(qc,bdd,output,constants,standard=0,alt_rtof=1):

    qubit_states = {}

    for i in range(len(qc.qubits)):                                      # generating qubit states
        qubit_states[qc.qubits[i].register.name + str(qc.qubits[i].index)] = bdd.add_expr(qc.qubits[i].register.name + str(qc.qubits[i].index))
    for qubit, state in constants.items():
        if state == '0':
            state = 'False'
        elif state == '1':
            state = 'True'
        qubit_states[qubit] = (bdd.add_expr(state)) #出力ビットを初期化

    qc_gates = retrieve_gates(qc)                                        # generating gates list

    total_phase = [bdd.add_expr('True'), bdd.add_expr('False'), bdd.add_expr('False'), bdd.add_expr('False')]  # total_phase初期化.
    bdd_pool = []   # for function search
    for gate in qc_gates:
        # print(qubit_states)
        #print("DCDEBUG gate_type " + gate[0])
        if gate[0] == 'cx':                                              # applying the individual gates
            qubit_states[gate[1][1]] = (qubit_states[gate[1][0]] & ~qubit_states[gate[1][1]]) | (~qubit_states[gate[1][0]] & qubit_states[gate[1][1]])
        elif gate[0] == 'x':
            qubit_states[gate[1][0]] = ~qubit_states[gate[1][0]]
        elif gate[0] == 'ccx' or gate[0] == 'mcx' or gate[0] == 'mcx_gray':
            #print("DCDEBUG gate_type " + gate[0])
            virtual_state = and_node(gate[1][:-2], qubit_states, bdd)
            #print("DCDEBUG virtual_state " + str(list(bdd.pick_iter(virtual_state))))
            #print("DCDEBUG gate[1][-1] " + gate[1][-1])
            if gate[1][-1] in output:       # if the phase change is in the ancilla bit, we need to calculate it
                #print("DCDEBUG gate in output")
                add_phase = [bdd.add_expr('True'), bdd.add_expr('False'), bdd.add_expr('False'), bdd.add_expr('False')]             # initializing add_phase
                                                                       # applying and gates to check which add_phase becomes true
                if(standard):                                                       
                    add_phase[1] = qubit_states[gate[1][0]] &   qubit_states[gate[1][1]] & ~ qubit_states[gate[1][2]]
                    add_phase[3] = qubit_states[gate[1][0]] &   qubit_states[gate[1][1]] &   qubit_states[gate[1][2]]
                    add_phase[2] = qubit_states[gate[1][0]] & ~ qubit_states[gate[1][-2]] &   qubit_states[gate[1][-1]]
                    add_phase[0] = ~(add_phase[1] | add_phase[2] | add_phase[3])
                else:
                    add_phase[2] = virtual_state & ~ qubit_states[gate[1][-2]] &   qubit_states[gate[1][-1]]
                    add_phase[0] = ~add_phase[2]
                    if(alt_rtof == 1):
                        add_phase_alt    = add_phase.copy()
                        add_phase_alt[2] = ~virtual_state & qubit_states[gate[1][-2]] &   qubit_states[gate[1][-1]]
                        add_phase   = pick_a_b(add_phase,add_phase_alt,total_phase,bdd)

                total_phase = proc_total_phase(add_phase,total_phase,bdd,standard)
                #print("DCDEBUG tmp calculate states")
                #for phase_func in total_phase:
                    #print("DCDEBUG " + str(list(bdd.pick_iter(phase_func))))

            if(standard):
                qubit_states[gate[1][2]]  = xor_node(qubit_states[gate[1][2]], qubit_states[gate[1][0]] & qubit_states[gate[1][1]],bdd)
            else:
                qubit_states[gate[1][-1]] = xor_node(qubit_states[gate[1][-1]], virtual_state & qubit_states[gate[1][-2]],bdd)

        target_func = bdd.add_expr('True') & qubit_states[gate[1][-1]]
        bdd_pool.append(target_func)    # pool bdd of each gate
    # print("DCDEBUG calculate states")
    # for phase_func in total_phase:
    #     print("DCDEBUG Expr" + str(bdd.to_expr(phase_func)))
    #     print("DCDEBUG " + str(list(bdd.pick_iter(phase_func))))
    return [qubit_states, total_phase, bdd, bdd_pool]


def synthesize(qc,outputs,regs,constants,standard=0,alt_rtof=1):
    bdd = cudd.BDD()
    var_arr  = []
    for qubit in qc.qubits:
        var_arr.append(qubit.register.name + str(qubit.index))
        bdd.declare(qubit.register.name + str(qubit.index))
    for i in range(4):
        var_arr.append('p' + str(i))
        bdd.declare('p' + str(i))
    qp     = QuantumRegister(4,"pi_2_")
    ret_qc = qc.copy()

    bdd_func  = calculate(qc,bdd,outputs,constants,standard,alt_rtof)
    #print("DCDEBUG bdd_func")
    #print(list(bdd.pick_iter(bdd_func[1][2])))
    ret_qc    = gen_phase_qc(ret_qc,bdd_func,bdd,regs)

    return ret_qc

def gen_phase_qc(qc,bdd_func,bdd,regs):
    ret_qc = qc.copy()
    #phase_func = bdd_func[1][2]
    phase_num = 0
    found = 0
    #print("DCDEBUG phase_func_len " + str(len(bdd_func)))
    for phase_func in bdd_func[1]:
        #print("DCDEBUG phase_num[" + str(phase_num) + "]")
        #print(list(bdd.pick_iter(phase_func)))

        if(func_exists_in_logic(phase_func,bdd_func[3]) or phase_func == bdd.add_expr('False')):
            # raise Exception("not implemented!")
            #print("DCDEBUG phase_num[" + str(phase_num) + "] is False")
            found = not phase_func == bdd.add_expr('False')
            #return [ret_qc,found]
        elif not phase_num == 0:
            bdd_pool = bdd_func[3]
            #print("DCDEBUG")
            #print(list(bdd.pick_iter(phase_func)))
            phase_qc = bdd_to_qc(bdd,phase_func,phase_num,qc, bdd_pool)
            #print("DCDEBUG phase_qc")
            #print(phase_qc.draw()) #DCDEBUG
            # print("DCDEBUG ret_qc")
            #print(ret_qc.draw()) #DCDEBUG
            ret_qc   = phase_qc.compose(ret_qc,qubits=qc.qubits)
            # print(ret_qc.draw()) #DCDEBUG
            # print(ret_qc)
        phase_num+=1

    # print("DCDEBUG final ret_qc")
    # print(ret_qc.draw()) #DCDEBUG

    return [ret_qc,found]

def func_exists_in_logic(phase_func, bdd_pool):
    for logic_func in bdd_pool:
        # print(phase_func == logic_func)
        if(phase_func == logic_func):
           return True
    return False

def bdd_to_qc(bdd,node,phase_num,qc, bdd_pool):
    ret_qc    = qc.copy()
    ret_qc.clear()
    #print("DCDEBUG len(node.support)" + str(len(node.support)))

    if(len(node.support) == 0):
        return ret_qc
    #print("DCDEBUG" + str(dedent(iter_to_bool(bdd,node))))
    cf = ClassicalFunction(dedent(iter_to_bool(bdd,node)))
    #phase_qc  = cf.synth(registerless=False,synthesizer=linear_synth)
    phase_qc  = cf.synth(registerless=False)

    min_qc = phase_qc
    min_phase_func = node
    cost = calc_cost.toffoli_to_rtof(phase_qc)
    # 各ループで論理一致するか探索したい
    for func in bdd_pool:
        phase_func = xor_node(func, node, bdd)
        cf = ClassicalFunction(dedent(iter_to_bool(bdd,phase_func)))
        phase_qc  = cf.synth(registerless=False)
        #print("DCDEBUG phase_qc")
        #print(phase_qc.draw())
        cost_tmp = calc_cost.toffoli_to_rtof(phase_qc)
        if cost > cost_tmp and not len(phase_qc.data) == 0:
            min_phase_func = phase_func
            cost = cost_tmp
            min_qc = phase_qc
    # return min_qc
    #print("DCDEBUG min_phase_func " + str(list(bdd.pick_iter(phase_func))))
    phase_qc = min_qc
    '''
    min_qc = phase_qc
    cost = calc_cost.toffoli_to_rtof(phase_qc)
    # 各ループで論理一致するか探索したい
    for i in range(len(bdd_pool)):
        func1 = bdd_pool[i]
        phase_func = xor_node(func1, node, bdd)
        cf = ClassicalFunction(dedent(iter_to_bool(bdd,phase_func)))
        phase_qc  = cf.synth(registerless=False)
        cost_tmp = calc_cost.toffoli_to_rtof(phase_qc)
        if cost > cost_tmp:
            # print("Cost Reduced:\t", cost, cost_tmp)
            cost = cost_tmp
            min_qc = phase_qc
        for j in range(i, len(bdd_pool)):
            func2 = bdd_pool[j]
            phase_func = xor_node(func2, phase_func, bdd)
            cf = ClassicalFunction(dedent(iter_to_bool(bdd,phase_func)))
            phase_qc  = cf.synth(registerless=False)
            cost_tmp = calc_cost.toffoli_to_rtof(phase_qc)
            if cost > cost_tmp:
                # print("Cost Reduced:\t", cost, cost_tmp)
                cost = cost_tmp
                min_qc = phase_qc
        # return min_qc
    phase_qc = min_qc
    '''
    # --------------------------------------
    phase_qubits = []
    #dizzynote:phase_qcともとqcの変数を合わすためのコード
    target_bit = 0
    for phase_qubit in phase_qc.qubits:
        found = 0
        function_assign = 0
        if(phase_qubit.register.name == "return"):
            target_bit = phase_qubit
            function_assign = 1
        for qubit in qc.qubits:
            if(function_assign == 1 and qubit.register.name + str(qubit.index) == "p" + str(phase_num)):
                phase_qubits.append(qubit)
                found = 1
            elif((qubit.register.name + str(qubit.index)) == phase_qubit.register.name):
                phase_qubits.append(qubit)
                found = 1
        if(found == 0):
            raise Exception("Did Not Find variable " + phase_qubit.register.name)
    # print(phase_qc.draw())
    # print(ret_qc.draw())
    phase_qc_inv = phase_qc.inverse()
    for i in range(phase_num):
        phase_qc.s(target_bit)

    phase_qc = phase_qc.compose(phase_qc_inv)


    ret_qc                      = ret_qc.compose(phase_qc,qubits=phase_qubits)
    
    return ret_qc

def and_node(qubit_list, qubit_states, bdd):
    assert(len(qubit_list) > 0)
    ret = bdd.add_expr('True')
    for qubit_num in qubit_list:
        ret = ret & qubit_states[qubit_num]
    return ret

def xor_node(node0,node1,bdd):

    return ~node0 & node1 | node0 & ~node1

#def bdd_to_bool(node,bdd):

def iter_to_bool(bdd,node):
    func_str = "def bool_exp("
    var_ct   = 0
    var_tot  = len(node.support)

    for var in node.support:
        var_strip = re.sub('\[|\]','',var)
        func_str = func_str + var_strip + ":Int1"
        if(var_ct < var_tot - 1):
            func_str = func_str + ", "
        var_ct+=1
    func_str = func_str + ")->Int1:\n"
    func_str = func_str + "\treturn ("
    statement_ct = 0
    iter_list    = list(bdd.pick_iter(node))
    # print(iter_list)
    iter_len     = len(iter_list)

    #print(iter_arr)
    for statement in iter_list:
        var_ct = 0
        func_str = func_str + "("
        for var in statement:
            var_strip = re.sub('\[|\]','',var)
            if(statement[var]):
                func_str = func_str + var_strip
            else:
                func_str = func_str + "(not " + var_strip + ")"
            if(var_ct < len(statement) - 1):
                func_str = func_str + " and "
            var_ct+=1
        func_str = func_str + ")"
        if(statement_ct < iter_len - 1):
            func_str = func_str + " or "
        statement_ct+=1
    if(len(iter_list) == 0):
        func_str = func_str + "False"
    #print("DCDEBUG func_str " + func_str)
    return func_str + ")\r"

def get_output(qc, garbage):
    output = []
    for i in range(len(garbage)):
        if garbage[i] == '-':
            output.append(qc.qubits[i].register.name + str(qc.qubits[i].index))

    return output

def get_constants(qc, constants_string):
    constants = {}
    for i in range(len(constants_string)):
        if constants_string[i] != '-':
            constants[qc.qubits[i].register.name + str(qc.qubits[i].index)] = constants_string[i]

    return constants

def proc_total_phase(add_phase, total_phase, bdd, standard):
    ret_total_phase = total_phase.copy()
    if(standard):
        tmp = ret_total_phase[3]
        ret_total_phase[3] = xor_node(ret_total_phase[3],(ret_total_phase[3] & add_phase[1]),bdd) | (add_phase[1] & ret_total_phase[(2)])
        ret_total_phase[2] = xor_node(ret_total_phase[2],(ret_total_phase[2] & add_phase[1]),bdd) | (add_phase[1] & ret_total_phase[(1)])
        ret_total_phase[1] = xor_node(ret_total_phase[1],(ret_total_phase[1] & add_phase[1]),bdd) | (add_phase[1] & ret_total_phase[(0)])
        ret_total_phase[0] = xor_node(ret_total_phase[0],(ret_total_phase[0] & add_phase[1]),bdd) | (add_phase[1] & tmp)

    tmp = ret_total_phase[0]
    ret_total_phase[0] = xor_node(ret_total_phase[0],(ret_total_phase[0] & add_phase[2]),bdd) | (add_phase[2] & ret_total_phase[(2)])
    ret_total_phase[2] = xor_node(ret_total_phase[2],(ret_total_phase[2] & add_phase[2]),bdd) | (add_phase[2] & tmp)

    if(standard):
        tmp = ret_total_phase[1]
        ret_total_phase[1] = xor_node(ret_total_phase[1],(ret_total_phase[1] & add_phase[2]),bdd) | (add_phase[2] & ret_total_phase[(3)])
        ret_total_phase[3] = xor_node(ret_total_phase[3],(ret_total_phase[3] & add_phase[2]),bdd) | (add_phase[2] & tmp)
                    
        tmp = ret_total_phase[0]
        ret_total_phase[0] = xor_node(ret_total_phase[0],(ret_total_phase[0] & add_phase[3]),bdd) | (add_phase[3] & ret_total_phase[(1)])
        ret_total_phase[1] = xor_node(ret_total_phase[1],(ret_total_phase[1] & add_phase[3]),bdd) | (add_phase[3] & ret_total_phase[(2)])
        ret_total_phase[2] = xor_node(ret_total_phase[2],(ret_total_phase[2] & add_phase[3]),bdd) | (add_phase[3] & ret_total_phase[(3)])
        ret_total_phase[3] = xor_node(ret_total_phase[3],(ret_total_phase[3] & add_phase[3]),bdd) | (add_phase[3] & tmp)

    return ret_total_phase

def pick_a_b(a,b,total_phase,bdd):
    #ヒューリスティックは、なるべく、１の数を2^(n-1)をさける
    a_tot   = proc_total_phase(a,total_phase,bdd,standard=0)
    b_tot   = proc_total_phase(b,total_phase,bdd,standard=0)
    #bdd.varsはscratch0とscratch1を含んでいる。それを無視する
    a_count = a_tot[2].count(len(bdd.vars) - 2)
    b_count = b_tot[2].count(len(bdd.vars) - 2)
    max_len = max(a_count,b_count)
    min_len = min(a_count,b_count)
    var_len = math.pow(2,len(bdd.vars) - 1)
    if( max_len > var_len):
        return (a if (max_len == a_count) else b)
    else:
        return (a if (min_len == a_count) else b)
    
    return a
