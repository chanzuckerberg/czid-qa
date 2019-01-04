#!/usr/bin/env python3
import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import os
from math import sqrt, log
from collections import defaultdict


EXIT_SUCCESS = 0


# ignore evalues larger than this
MAX_EVALUE = 1e-10


class RunningStats:
    """Accumulate running stats (count, mean, stddev) efficiently."""

    def __init__(self):
        # running count
        self.count = 0
        # running mean
        self.m = 0.0
        # running variance (second moment)
        self.m2 = 0.0

    def accumulate(self, new_value):
        self.count += 1
        delta = new_value - self.m
        self.m += delta / self.count
        delta2 = new_value - self.m
        self.m2 += delta * delta2

    def stddev(self):
        if self.count <= 1:
            return 0.0
        return sqrt(self.m2 / (self.count - 1))

    def mean(self):
        return self.m


def neglog10(evalue):
    "Per idseq.net convention, we report -log_10(evalue)."
    return -log(evalue)/log(10)


def main(argv):
    print(f"Crunching gsnap output from stdin")
    pairs = {}
    reads = {}
    if "pairs" in argv:
        print("Will report read pairs instead individual reads.")
    for line in sys.stdin:
        if line.count(':') > 4:  # empirical indicator this is a read output and not some debug print
            parts = line.split()
            read_id = parts[0]
            pair_id = read_id[:-2]
            accession = parts[1]
            evalue = float(parts[10])
            if evalue > MAX_EVALUE:
                continue
            if pair_id not in pairs or pairs[pair_id] > (evalue, accession):
                pairs[pair_id] = (evalue, accession)
            if read_id not in reads or reads[read_id] > (evalue, accession):
                reads[read_id] = (evalue, accession)
    accessions = defaultdict(RunningStats)
    if "pairs" in argv:
        items = pairs
    else:
        items = reads
    for iid in sorted(items):
        evalue, accid = items[iid]
        # print(f"{pid}\t{accid}\t{evalue}")
        accessions[accid].accumulate(neglog10(evalue))
    for accid, stats in sorted(accessions.items(), key=lambda it: (it[1].count, it[0])):
        print(f"{accid}\t{stats.count:4}\t{stats.mean():.1f}") #\t{stats.stddev():4.4}")
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        exitcode = main(sys.argv)
    except:
        print("USAGE:  See https://github.com/chanzuckerberg/idseq-qa/blob/master/README.md")
        raise
    os.sys.exit(exitcode)
