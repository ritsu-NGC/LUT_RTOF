from blif_read import comp_methods
import sys
import time
import glob
import csv
import time

def dict_to_latex(dct):
    # Get the keys and values from the dictionary
    keys = list(dct.keys())
    values = []
    latex_table = ""
    values = [str(val).replace('_','\_') for val in dct.values()]

    # Add the data rows to the LaTeX table
    latex_table += " & ".join(values)
    latex_table += " \\\\\n"
    latex_table += "\\hline\n"

    # End the LaTeX table string


    # Return the LaTeX table string
    return latex_table

def write_latex(fpath,results):
    # Initialize the LaTeX table string
    keys     = results[0].keys()
    num_cols = len(keys)
    latex_table = "\\begin{tabular}{|" + "c|" * num_cols + "}\n"
    latex_table += "\\hline\n"

    # Add the header row to the LaTeX table
    header_row = " & ".join([str(key) for key in keys])
    latex_table += header_row + " \\\\\n"
    latex_table += "\\hline\n"

    for result in results:
        latex_table += dict_to_latex(result)
    latex_table += "\\end{tabular}\n"

    f = open(fpath,'w')
    print(latex_table,file=f)

def write_csv(CSV_FILE, data):
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        header = []
        for key in data[0]:
            header.append(key)
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        writer.writerows(data)

def run_tests(rundir):
    #benchmark_circuits = glob.glob(rundir + "/*.blif")
    now = time.localtime()
    time_str = time.strftime('%Y-%m-%d_%H-%M', now)
    CSV_FILE = "result_" + time_str + ".csv"
    TEX_FILE = "result_" + time_str + ".tex"
        
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
        for field in result_tmp:
            print(field + " " + str(result_tmp[field]))
        # print(result_tmp['Circuit'] + " cost " + str(result_tmp['Proposed']))
        # print(result_tmp['Circuit'] + " cf_cost " + str(result_tmp['ESOP']))
        # print(result_tmp['Circuit'] + " NeedAncilla " + str(result_tmp['NeedAncilla']))
        # print(result_tmp['Circuit'] + " TotalAncilla " + str(result_tmp['TotalAncilla']))        

    write_csv(CSV_FILE, results)
    write_latex(TEX_FILE,results)

if __name__ == '__main__':
    rundir = sys.argv[1]
    run_tests(rundir)
