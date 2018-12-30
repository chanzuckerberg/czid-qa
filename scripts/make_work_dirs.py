#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import os
import json
from util import smart_ls, check_output


EXIT_SUCCESS = 0
DEBUG = False

RUN_TEMPLATE = """\
#!/bin/bash
now=`date +%s`
h=`pwd`
log=run-$$-$now.log
rm -f $log
dest=/home/ubuntu/batch-pipeline-workdir/{WORKDIR_TAIL}-$$-$now
rm -rf $dest
r1={R1}
r2={R2}
mkdir -p $dest
cp $r1 $dest/
cp $r2 $dest/
cd $dest
nohup time /home/ubuntu/g_gsnap/gmap-2018-10-26/src/gsnapl.avx2 --time -A m8 --batch=0 --use-shared-memory=0 --gmap-mode=none --npaths=100 --ordered -t 24 --max-mismatches=40 -D /home/ubuntu/share/2018-12-01 -d nt_k16 $r1 $r2 >$here/$log 2>&1 &
cd $h
echo "Job started.  To watch its log, use the command below."
echo "tail -f $h/$log"
"""

CONTINUOUSLY_RUN_TEMPLATE = """\
#!/bin/bash
while :
do
  date
  pgrep -f {R1} && echo gsnap is already running on {R1} || ./run.sh
  sleep 5
done
"""


def parse(chunk):
    # each chunk is represented by two files, with names
    #     sample-NNNNN-gsnap_filter_{1,2}.fa-chunksize-MMMMMM-numparts-YY-part-XX
    tokens = chunk.split("-")
    assert tokens[0] == "sample"
    assert tokens[1].isnumeric()
    assert tokens[2] in ["gsnap_filter_1.fa", "gsnap_filter_2.fa", "subsampled_1.fa", "subsampled_2.fa"]
    assert tokens[3] == "chunksize"
    assert tokens[4].isnumeric()
    assert tokens[5] == "numparts"
    assert tokens[6].isnumeric()
    assert tokens[7] == "part"
    assert tokens[8].isnumeric()
    assert len(tokens) == 9
    # return sample_id, part_idx, r1/r2 designator
    # used as key this ensures r1 and r2 appear consecutively in the sort order
    return (tokens[1], tokens[8], tokens[2])


def main(argv):
    downloaded_chunks_path = argv[1]
    workdir_root = argv[2]
    print(f"Instantiating work dirs under '{workdir_root}' for each chunk in '{downloaded_chunks_path}'.")
    chunks = sorted(smart_ls(downloaded_chunks_path, quiet=True), key=parse)
    r1_list = chunks[0::2]
    r2_list = chunks[1::2]
    for r1, r2 in zip(r1_list, r2_list):
        sample_id, part_idx, d = parse(r1)
        sample_id_2, part_idx_2, d2 = parse(r2)
        assert (sample_id, part_idx) == (sample_id_2, part_idx_2)
        workdir_tail = f"repro_{sample_id}_{part_idx}"
        workdir = f"{workdir_root}/{workdir_tail}"
        os.makedirs(workdir, exist_ok=False)
        for chunk in [r1, r2]:
            os.link(f"{downloaded_chunks_path}/{chunk}", f"{workdir}/{chunk}")
        scripts = [
            ("run.sh", RUN_TEMPLATE.format(R1=r1, R2=r2, WORKDIR_TAIL=workdir_tail)),
            ("continuously_run.sh", CONTINUOUSLY_RUN_TEMPLATE.format(R1=r1))
        ]
        for script_name, script_code in scripts:
            with open(f"{workdir}/{script_name}", "w") as scrif:
                scrif.write(script_code)
            check_output(f"chmod a+x {workdir}/{script_name}", quiet=True)
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        exitcode = main(sys.argv)
    except:
        print("USAGE:  See https://github.com/chanzuckerberg/idseq-qa/blob/master/README.md")
        raise
    os.sys.exit(exitcode)
