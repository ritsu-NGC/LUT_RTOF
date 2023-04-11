from blif_read import comp_methods
import sys
import time
import glob
def write_latex(fpath,results):
    print("results")
def run_tests(rundir):
    #benchmark_circuits = glob.glob(rundir + "/*.blif")
    benchmark_circuits = [str(rundir + "/priority_size_2022.blif"),
                          str(rundir + "/int2float_size_2022.blif"),
                          str(rundir + "/i2c_size_2022.blif"),
                          str(rundir + "/dec_size_2018.blif"),
                          str(rundir + "/ctrl_size_2022.blif"),
                          str(rundir + "/cavlc_size_2022.blif"),
                          str(rundir + "/bar_size_2015.blif"),
                          str(rundir + "/arbiter_size_2022.blif"),
                          str(rundir + "/adder_size_2022.blif")]
    # benchmark_circuits = [str(rundir + "/router_size_2022.blif"),
    #                       str(rundir + "/priority_size_2022.blif"),
    #                       str(rundir + "/int2float_size_2022.blif"),
    #                       str(rundir + "/i2c_size_2022.blif"),
    #                       str(rundir + "/dec_size_2018.blif"),
    #                       str(rundir + "/ctrl_size_2022.blif"),
    #                       str(rundir + "/cavlc_size_2022.blif"),
    #                       str(rundir + "/bar_size_2015.blif"),
    #                       str(rundir + "/arbiter_size_2022.blif"),
    #                       str(rundir + "/adder_size_2022.blif")]
    results = []
    for circuit in benchmark_circuits:
        start = time.time()
        print(circuit.split('/')[-1].split('.')[0])
        result_tmp = comp_methods(circuit)
        results.append(result_tmp)
        print(result_tmp['Circuit'] + " cost " + str(result_tmp['Proposed']))
        print(result_tmp['Circuit'] + " cf_cost " + str(result_tmp['ESOP']))

    write_latex('table.tex',results)

if __name__ == '__main__':
    rundir = sys.argv[1]
    run_tests(rundir)
