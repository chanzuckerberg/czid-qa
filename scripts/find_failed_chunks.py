#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import os
import json
from util import smart_ls


EXIT_SUCCESS = 0


DEBUG = False


def parse_project_path(argv):
    ENVIRONMENTS = ["staging", "prod", "development", "test"]
    expected_prefixes = [f"s3://idseq-samples-{env}/samples" for env in ENVIRONMENTS]
    try:
        argument = argv[1]
        actual_prefix, project_id_str = argument.strip().strip("/").rsplit("/", 1)
        assert actual_prefix in expected_prefixes
        assert str(int(project_id_str)) == project_id_str
        project_id = int(project_id_str)
        return f"{actual_prefix}/{project_id}"
    except:
        cmd_line = " ".join(argv[1:])
        print(f"ERROR:  Could not parse project path from command line argument.  Expected 's3://idseq-samples-<environment>/samples/<project_id>', found '{cmd_line}'.")
        raise


def looks_like_version(item):
    return all(part.isnumeric() for part in item.split("."))


def find_dirs(items):
    for d in items:
        if d.endswith("/"):
            yield d[:-1]


def find_samples_results(project_path):
    for sample_dir in find_dirs(smart_ls(project_path, missing_ok=False, quiet=True)):
        for version_dir in find_dirs(smart_ls(f"{project_path}/{sample_dir}/results", missing_ok=False, quiet=True)):
            if looks_like_version(version_dir):
                yield f"{project_path}/{sample_dir}/results/{version_dir}"


def drop(prefix, s, suffix):
    assert s.startswith(prefix)
    assert s.endswith(suffix)
    return s[len(prefix) : len(s) - len(suffix)]


def main(argv):
    project_path = parse_project_path(argv)
    print(f"Scoring project {project_path}.")
    GSNAP_M8_PREFIX = "multihit-gsnap-out-"
    GSNAP_FA_PREFIX = "gsnap_filter_1.fa-"
    GSNAP_ALT_PREFIX = "subsampled_1.fa-"
    project_failed_chunks = 0
    project_total_chunks = 0
    print("--------------------------------------------------------------------------------------------------------")
    for sample_results_path in find_samples_results(project_path):
        sample_chunks = smart_ls(f"{sample_results_path}/chunks", missing_ok=True, quiet=True)
        sample_chunks = [
            c.replace(GSNAP_ALT_PREFIX, GSNAP_FA_PREFIX) if c.startswith(GSNAP_ALT_PREFIX) else c
            for c in sample_chunks
        ]
        read_1_chunk_ids = set(
            drop(GSNAP_FA_PREFIX, c, "")
            for c in sample_chunks
            if c.startswith(GSNAP_FA_PREFIX)
        )
        gsnap_success_ids = set(
            drop(GSNAP_M8_PREFIX, c, ".m8")
            for c in sample_chunks
            if c.startswith(GSNAP_M8_PREFIX)
        )
        if not sample_chunks:
            print(f"Found no gsnap chunks at all for {sample_results_path}")
        else:
            num_failed = len(read_1_chunk_ids ^ gsnap_success_ids)
            num_total = len(read_1_chunk_ids)
            project_failed_chunks += num_failed
            project_total_chunks += num_total
            percent_failed = 100.0 * num_failed / num_total
            print(f"Found {num_failed:3} failed of {num_total:3} total gsnap chunks ({percent_failed:3.0f}% failure rate) under {sample_results_path}.")
            if DEBUG:
                print(json.dumps(sorted(read_1_chunk_ids ^ gsnap_success_ids), indent=4).replace("\n", "    \n"))
    percent_failed = 100.0 * project_failed_chunks / project_total_chunks
    print("--------------------------------------------------------------------------------------------------------")
    print(f"Found {project_failed_chunks} failed of {project_total_chunks} total gsnap chunks ({percent_failed:3.0f}% failure rate) under project {project_path}.")
    #print(json.dumps(samples_results_paths, indent=4))
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        exitcode = main(sys.argv)
    except:
        print("USAGE:  See https://github.com/chanzuckerberg/idseq-qa/blob/master/README.md")
        raise
    os.sys.exit(exitcode)
