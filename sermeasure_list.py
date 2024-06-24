#
# list of SerMeasure-inherited class
#
from m1 import M1, M2, M3
from tpg36x import TPG36X
from ls335 import LS335
from ls218 import LS218
from tic100 import TIC100
from bcg450 import BCG450
from vsm7xx import VSM7XX

import inspect, sys

serm_class_list = []
for name, obj in inspect.getmembers(sys.modules[__name__]):          
    if inspect.isclass(obj) and obj.__base__.__name__ == 'SerMeasure':
        serm_class_list.append(obj)
serm_name_list = [x.__name__ for x in serm_class_list]

if __name__=="__main__":
    print(serm_class_list)
    print(serm_name_list)