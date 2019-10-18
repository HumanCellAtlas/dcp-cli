import csv


# Wrap the csv library with our required options

def DictReader(f):
    return csv.DictReader(f, delimiter='\t', dialect='excel-tab')


def DictWriter(f, fieldnames):
    return csv.DictWriter(f, fieldnames, delimiter='\t', dialect='excel-tab')
