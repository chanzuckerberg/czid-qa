# IDseq QA
Custom tools to QA new releases of gsnap, rapsearch, STAR, or any other bioinformatics tool used in the [IDseq pipeline.](https://github.com/chanzuckerberg/idseq-dag/)

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
