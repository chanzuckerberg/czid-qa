# CZ ID QA
Custom tools to QA new releases of gsnap, rapsearch, STAR, or any other bioinformatics tool used in the [CZ ID pipeline.](https://github.com/chanzuckerberg/czid-dag/)

This repo is formerly known as idseq-qa

# Example use

1. Find and download all failed chunks in project 232.
```
    > mkdir failed_chunks
    > cd failed_chunks
    > /path/to/idseq-qa/scripts/find_failed_chunks.py s3://idseq-samples-staging/samples/232 download
    > cd ..

    Scoring project s3://idseq-samples-staging/samples/232.
    --------------------------------------------------------------------------------------------------------
    Found   0 failed of   7 total gsnap chunks (  0% failure rate) under s3://idseq-samples-staging/samples/232/11751/results/3.2.
    Found   1 failed of  17 total gsnap chunks (  6% failure rate) under s3://idseq-samples-staging/samples/232/11752/results/3.2.
    Found   1 failed of   6 total gsnap chunks ( 17% failure rate) under s3://idseq-samples-staging/samples/232/11753/results/3.2.
    Found  27 failed of  27 total gsnap chunks (100% failure rate) under s3://idseq-samples-staging/samples/232/11754/results/3.2.
    Found   0 failed of  11 total gsnap chunks (  0% failure rate) under s3://idseq-samples-staging/samples/232/11755/results/3.2.
    Found   5 failed of  13 total gsnap chunks ( 38% failure rate) under s3://idseq-samples-staging/samples/232/11756/results/3.2.
    Found   0 failed of   1 total gsnap chunks (  0% failure rate) under s3://idseq-samples-staging/samples/232/11757/results/3.2.
    Found   0 failed of   1 total gsnap chunks (  0% failure rate) under s3://idseq-samples-staging/samples/232/11758/results/3.2.
    --------------------------------------------------------------------------------------------------------
    Found 34 failed of 83 total gsnap chunks ( 41% failure rate) under project s3://idseq-samples-staging/samples/232.    
```

2. Run downloaded chunks repeatedly to repro failures.
```
    > mkdir workdir
    > /path/to/idseq-qa/scripts/make_work_dirs.py failed_chunks workdir
```
This will create folders `workdir/repro_XXXXX_YY` for all `failed_chunks`.  To run one chunk continuously,
```
    > cd workdir/repro_XXXXX_YY
    > nohup ./continuously_run.sh &
    > tail -f nohup.out
```

3. To run a new version of gsnap on reads classified a certain way by an older verison,
first download the fasta from idseq, then strip it of annotations and split it into
r1 and r2 files as follows:
```
cat patient_11_prod_70_4534_torque-teno-midi-virus-11-hits.fasta | ./reverse_idseq.py r1.fa r2.fa
```

4. Rank accessions in gsnap's m8 output according to how many read pairs they win.  An accession wins a pair by having the min evalue emitted by gsnap for either end of the pair.  For each winning accession, output the number of pairs it won, and the mean -log10(1/evalue) across all its wins.
```
    >cat gsnap2017ttmv.m8 | m8_group_by_accid.py pairs
    Crunching gsnap output from stdin
    Will report read pairs instead individual reads.
    AB290917.1	   1	86.4
    AB303552.1	   1	89.1
    AB303563.1	   4	46.3
    EF538876.1	   6	89.1
    AB303553.1	  16	82.6
    AB303561.1	  19	39.9
    HQ677732.1	  30	40.5
    AB303565.1	  36	83.9
    AB303555.1	  44	59.3
    AB303564.1	  44	78.4
    AB303566.1	  75	62.1
    AB290920.1	 271	85.5
    JQ734975.1	 345	44.5
    EF538875.1	 481	75.7
    AB290918.1	 894	88.1
    JX157237.1	 928	77.8
```
Optionally, omit the `pairs` keyword in the command to operate on individual reads.
