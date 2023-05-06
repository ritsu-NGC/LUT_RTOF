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
for field in costs:
    print(field + " " + str(costs[field]))
# print("cost " + str(costs['Proposed']))
# print("cf_cost " + str(costs['ESOP']))
# print("NeedAncilla " + str(costs['NeedAncilla']))
# print("TotalAncilla " + str(costs['TotalAncilla']))
