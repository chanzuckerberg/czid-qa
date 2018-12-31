#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import os
import json
from util import smart_ls, check_output


EXIT_SUCCESS = 0
DEBUG = False
UNCLASSIFIED_GENUS = "genus_nt:-200"
UNSUPPORTED_FORMAT = "Cannot handle this input fasta format."


def parse(annotated_header):
    assert annotated_header.split(":")[::2][:8] == ['>family_nr', 'family_nt', 'genus_nr', 'genus_nt', 'species_nr', 'species_nt', 'NR', 'NT']
    # This looks like 'A00111:122:HCMCVDMXX:1:1103:9091:10942/1' or '..../2'
    post_gsnap_header = ":".join(annotated_header.split(":")[16:])
    original_header, end_str = post_gsnap_header.rsplit("/", 1)
    end = int(end_str)
    assert end in (1, 2)
    return (original_header, end - 1)


def main(argv):
    r1fn = argv[1]
    r2fn = argv[2]
    print(f"Removing idseq tags, gsnap /1 and /2 prefixes, and splitting read pairs from stdin.")
    reads = {}
    unclassified = set()
    while True:
        annotated_header = sys.stdin.readline().strip()
        sequence = sys.stdin.readline().strip()
        if not annotated_header:
            break
        assert annotated_header.startswith(">"), UNSUPPORTED_FORMAT
        assert sequence, UNSUPPORTED_FORMAT
        assert not sequence.startswith(">"), UNSUPPORTED_FORMAT
        orig_header, end = parse(annotated_header)
        if orig_header not in reads:
            reads[orig_header] = [None, None]
        assert reads[orig_header][end] == None, f"Duplicate read ID {header}/{end}"
        if UNCLASSIFIED_GENUS in annotated_header:
            unclassified.add(orig_header)
        else:
            reads[orig_header][end] = sequence
    print(f"Read {len(reads)} paired-end reads.")
    incomplete_pairs = 0
    with open(r1fn, "w") as r1,\
         open(r2fn, "w") as r2:
        for header, ends in reads.items():
            if not ends[0] or not ends[1]:
                # print(f"Incomplete read pair for {header}")
                incomplete_pairs += 1
            else:
                r1.write(">" + header + "\n")
                r1.write(reads[header][0] + "\n")
                r2.write(">" + header + "\n")
                r2.write(reads[header][1] + "\n")
    x1 = len(unclassified)
    x2 = incomplete_pairs - len(unclassified)
    print(f"Emitted {len(reads) - incomplete_pairs} read pairs.")
    print(f"Excluded {x1+x2} pairs due to incomplete classification:")
    print(f"    {x2:3} pairs ({100.0*x2/len(reads):3.1f}%) in which one end is missing or unclassified.")
    print(f"    {x1:3} pairs ({100.0*x1/len(reads):3.1f}%) in which both ends are unclassified.")
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        exitcode = main(sys.argv)
    except:
        print("USAGE:  See https://github.com/chanzuckerberg/idseq-qa/blob/master/README.md")
        raise
    os.sys.exit(exitcode)
