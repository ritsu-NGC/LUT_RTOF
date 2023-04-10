import sys
import tracemalloc

#tracemalloc.start(10)

from blif_read import comp_methods

filename = sys.argv[1]
costs = comp_methods(filename)
#try:
#except:
#    snapshot = tracemalloc.take_snapshot()
#    print(snapshot)
print("cost " + str(costs['Proposed']))
print("cf_cost " + str(costs['ESOP']))
