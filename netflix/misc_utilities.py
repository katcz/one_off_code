#!/usr/bin/python3

from contextlib import contextmanager
@contextmanager
def temp_plt_figure(*args, **kwargs):
    import matplotlib.pyplot as plt
    figure = plt.figure(*args, **kwargs)
    yield figure
    plt.close(figure)

from typing import Callable
from contextlib import contextmanager
@contextmanager
def timer(section_name: str = None, exitCallback: Callable[[], None] = None):
    import time
    start_time = time.time()
    yield
    end_time = time.time()
    elapsed_time = end_time - start_time
    if exitCallback != None:
        exitCallback(elapsed_time)
    elif section_name:
        print(f'{section_name} took {elapsed_time} seconds.')
    else:
        print(f'Execution took {elapsed_time} seconds.')

from typing import Iterable
from collections import Counter
def histogram(iterator: Iterable) -> Counter:
    from collections import Counter
    counter = Counter()
    for element in iterator:
        counter[element]+=1
    return counter

from typing import Callable
def debug_on_error(func: Callable) -> Callable:
    import pdb
    import traceback
    import sys
    def decorating_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            print(f'Exception Class: {type(err)}')
            print(f'Exception Args: {err.args}')
            extype, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
    return decorating_function