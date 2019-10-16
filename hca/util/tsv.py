import csv
import functools


# Wrap the csv library with our required options

DictReader = functools.partial(csv.DictReader, delimiter='\t', dialect='excel-tab')
DictWriter = functools.partial(csv.DictWriter, delimiter='\t', dialect='excel-tab')
