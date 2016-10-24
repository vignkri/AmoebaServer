"""
Utilities
"""
import itertools


# Create groups from data
def grouper(n, iterable, fillVal=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(fillvalue=fillVal, *args)
