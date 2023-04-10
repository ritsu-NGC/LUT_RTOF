from dd import cudd
import queue

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.tools.visualization import circuit_drawer
import math
def gen_rev_qc(qc,output):
    rev_gates = []
    for gate in qc.data:
        output_qubit = gate[1][-1].register.name + str(gate[1][-1].index)
        if(output_qubit in output):
            rev_gates.append(gate.copy())
    ret_qc = qc.copy()
    ret_qc.barrier()
    for i in range(len(rev_gates)-1,-1,-1):
        ret_qc.append(rev_gates[i])
    return ret_qc 

def retrieve_gates(qc):

    # Takes a QuantumCircuit object as input, and returns a list of gates in the circuit, in the order they act in the circuit.
    # Each gate is of the format (list) [(string) gateName, (list) QubitIndices]
    # The QubitIndices follow the same format as the Qiskit QuantumCircuit
    # Gates

    gates_list = []
    for gate in qc.data:
        temp_list = []
        temp_list.append(gate[0].name)
        qubit_list = []
        
        for i in range(len(gate[1])):
            qubit_list.append(gate[1][i].register.name + str(gate[1][i].index))
        temp_list.append(qubit_list)
        #temp_list.append(gate)
        gates_list.append(temp_list)
    return gates_list


def not_bdd(qubit):
    # Takes a qubit as input, and returns the string representation of the NOT gate on that qubit
    # Brackets are added to prevent ambiguity in the string representation of
    # the circuit
    if (qubit == 'True'):
        return 'False'
    if (qubit == 'False'):
        return 'True'
    qubit = '( ~ ' + qubit + ' )'
    return qubit


def and_bdd(qubit_one, qubit_two):
    # Takes a qubit as input, and returns the string representation of the NOT gate on that qubit
    # Brackets are added to prevent ambiguity in the string representation of
    # the circuit
    return qubit_one & qubit_two;


def or_bdd(qubit_one, qubit_two):
    # Takes a qubit as input, and returns the string representation of the NOT gate on that qubit
    # Brackets are added to prevent ambiguity in the string representation of
    # the circuit
    if (qubit_one == 'True') or (qubit_two == 'True'):
        return 'True'

    if (qubit_one == 'False'):
        return qubit_two
    if (qubit_two == 'False'):
        return qubit_one

    qubit = '( ' + qubit_one + ' \\/ ' + qubit_two + ' )'

    return qubit_one | qubit_two


def cnot_bdd(qubit_control, qubit_target):
    qubit_target = ' ( ( ~ ' + qubit_target + ' ) /\\ ' + qubit_control + \
                   ' ) \\/ ( ' + qubit_target + ' /\\ ( ~ ' + qubit_control + ' ) )'
    return qubit_target


def toffoli_bdd(qubit_control_one, qubit_control_two, qubit_target):
    # Takes a qubit as input, and returns the string representation of the Toffoli gate with first two arguments as control bits and the third as target bits
    # Brackets are added to prevent ambiguity in the string representation of
    # the circuit

    qubit_target = ' ( ( ~ ' + qubit_target + ' )' + ' /\\ ( ' + qubit_control_one + ' /\\ ' + qubit_control_two + ' ) ) ' + \
                   '\\/ ( ' + qubit_target + ' /\\' + ' ( ~ ( ' + qubit_control_one + ' /\\ ' + qubit_control_two + ' ) ) )'
    return qubit_target



def get_qc_bdd(qc,bdd):
    # 量子回路をbddに変換
    qubit = []
    #bdd = _bdd.BDD()

    for i in range(qc.num_qubits):
        name = "q"+str(i)
        bdd.declare(name)
        qubit.append(bdd.add_expr(name))
        # 変数としての量子ビット、変数宣言
    gate_list = retrieve_gates(qc)
    # すべてのドアを手に入れる
    for gate in gate_list:
        if gate[0] == "x":
            qubit[gate[1][0]] = ~qubit[gate[1][0]]
        elif gate[0] == 'cx':
            qubit[gate[1][1]] = (~qubit[gate[1][0]] & qubit[gate[1][1]]) | (qubit[gate[1][0]] & ~qubit[gate[1][1]])
        if gate[0] == 'ccx':
            qubit[gate[1][2]] = (qubit[gate[1][0]] & qubit[gate[1][1]] &  ~qubit[gate[1][2]]) | qubit[gate[1][2]]
    # ゲートに従って量子ビットの論理関係を構築する

    return qubit

def convert_rtof(qc):
    #ret_qr = QuantumRegister(bits=qc.qubits)
    #ret_qc = QuantumCircuit(qr)
    ret_qc = qc.copy()
    ret_qc.clear()
    flip = 0
    for gate in qc.data:
        print(gate)
        if((gate[0].name == "ccx")):
            print(flip)
            if(flip==0):
                rtof = get_rtof(qc,gate[1][0],gate[1][1],gate[1][2]).to_instruction(label="rtof")
            else:
                #print("DCDEBUG rtofdg")
                #print(get_rtof(qc,gate[1][0],gate[1][1],gate[1][2]).inverse().draw())
                rtof = get_rtof(qc,gate[1][0],gate[1][1],gate[1][2]).inverse().to_instruction(label="rtofdg") 
                #rtof = get_rtof_inv(qc,gate[1][0],gate[1][1],gate[1][2]).to_instruction(label="rtofdg")
            ret_qc.append(rtof,qc.qubits)
        elif(gate[0].name == "barrier"):
            flip = 1 #barrierを含まない
        else:
            ret_qc.append(gate[0], gate[1])

    return ret_qc
    
def get_rtof(qc,x0,x1,f):
    #ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    #DCDEBUG ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.t(f)
    ret_qc.cx(x1,f)
    ret_qc.tdg(f)
    ret_qc.cx(x0,f)
    ret_qc.t(f)
    ret_qc.cx(x1,f)
    ret_qc.tdg(f)
    ret_qc.h(f)
    #DCDEBUG ret_qc.sdg(f)
    #print("DCDEBUG get_rtof")
    #print(ret_qc.draw())
    return ret_qc

def get_rtof_alt(qc,x0,x1,f):
    #ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    #DCDEBUG ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.cx(x0,f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.h(f)
    #DCDEBUG ret_qc.sdg(f)
    #print("DCDEBUG get_rtof")
    #print(ret_qc.draw())
    return ret_qc

def get_rtof_inv(qc,x0,x1,f):
#    ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.cx(x0,f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.h(f)    
    ret_qc.sdg(f)
    return ret_qc.to_instruction(label="rtofdg")
