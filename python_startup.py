import pdb
import traceback
import sys
import os
import time
import signal
from functools import reduce
from contextlib import contextmanager
from itertools import chain, combinations
from typing import Iterable, Callable, Generator

# Start Up Prints

def print_header() -> None:
    print(f'')
    print(f'Start time: {time.strftime("%Y/%m/%d %H:%M:%S")}')
    print(f'Current Working Directory: {os.getcwd()}')
    print(f'')
    print(f'''Useful Forms:

import metagraph_cuda.tests.algorithms.test_pagerank ; from importlib import reload ; reload(metagraph_cuda.tests.algorithms.test_pagerank) ; from metagraph_cuda.tests.algorithms.test_pagerank import *

os.chdir(os.path.expanduser('~/code/one_off_code/cugraph_experiments/')); import test_community, importlib; importlib.reload(test_community); from test_community import * 

@debug_on_error
def test():
    import test_community, importlib; importlib.reload(test_community)
    return test_subgraph_extraction()
''')
    return

print_header()

# Printing Utilities

def p1(iterable: Iterable) -> None:
    for e in iterable:
        print(e)
    return

# Debugging Utilities

def debug_on_error(func: Callable) -> Callable:
    def func_wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as err:
            print(f'Exception Class: {type(err)}')
            print(f'Exception Args: {err.args}')
            extype, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
    return func_wrapped

# Timing Utilities

@contextmanager
def timeout(time: float, functionToExecuteOnTimeout: Callable[[], None] = None):
    """NB: This cannot be nested."""
    def _raise_timeout(*args, **kwargs):
        raise TimeoutError
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(time)
    try:
        yield
    except TimeoutError:
        if functionToExecuteOnTimeout is not None:
            functionToExecuteOnTimeout()
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)

@contextmanager
def timer(section_name: str = None, exitCallback: Callable[[], None] = None):
    start_time = time.time()
    yield
    end_time = time.time()
    elapsed_time = end_time - start_time
    if exitCallback != None:
        exitCallback(elapsed_time)
    elif section_name:
        print('Execution of "{section_name}" took {elapsed_time} seconds.'.format(section_name=section_name, elapsed_time=elapsed_time))
    else:
        print('Execution took {elapsed_time} seconds.'.format(elapsed_time=elapsed_time))

# General Utilities

def identity(input):
    return input

def implies(antecedent: bool, consequent: bool) -> bool:
    return not antecedent or consequent

UNIQUE_BOGUS_RESULT_IDENTIFIER = (lambda x: x)

def uniq(iterator: Iterable) -> Generator:
    previous = UNIQUE_BOGUS_RESULT_IDENTIFIER
    for value in iterator:
        if previous != value:
            yield value
            previous = value

def powerset(iterable: Iterable) -> Iterable:
    items = list(iterable)
    number_of_items = len(items)
    subset_iterable = chain.from_iterable(combinations(items, length) for length in range(1, number_of_items+1))
    return subset_iterable

def n_choose_k(n, k):
    k = min(k, n-k)
    numerator = reduce(int.__mul__, range(n, n-k, -1), 1)
    denominator = reduce(int.__mul__, range(1, k+1), 1)
    return numerator // denominator

def false(*args, **kwargs) -> bool:
    return False

def current_timestamp_string() -> str:
    return time.strftime("%Y_%m_%d_%H_%M_%S")

def unzip(zipped_item: Iterable) -> Iterable:
    return zip(*zipped_item)