from circuit_to_logic import retrieve_gates

def count_t(qc):
    GCount = 0
    qc_gates = retrieve_gates(qc)
    for type, qubit_list in qc_gates:
        if len(qubit_list) >= 3:
            GCount += 1
    return GCount

def all_toffoli(qc):
    Tcount = 0
    qc_gates = retrieve_gates(qc)
    for type, qubit_list in qc_gates:
        if len(qubit_list) == 3:
            Tcount += 7
        elif len(qubit_list) > 3:
            Tcount += (len(qubit_list)-3) * 2 * 7
            Tcount += 7
    return Tcount


def conventional_cost(qc, output):
    Tcount = 0
    qc_gates = retrieve_gates(qc)
    for type, qubit_list in qc_gates:
        if len(qubit_list) == 3:
            if qubit_list[-1] in output:
                Tcount += 7
            else:
                Tcount += 4
        elif len(qubit_list) > 3:
            Tcount += (len(qubit_list)-3) * 2 * 4
            if qubit_list[-1] in output:
                Tcount += 7
            else:
                Tcount += 4
    return Tcount


def toffoli_to_rtof(qc):
    Tcount = 0
    qc_gates = retrieve_gates(qc)
    for type, qubit_list in qc_gates:
        # print(type, qubit_list)
        if len(qubit_list) == 3:
            Tcount += 4
        elif len(qubit_list) > 3:
            Tcount += (len(qubit_list)-3) * 2 * 4
            Tcount += 4
    return Tcount
