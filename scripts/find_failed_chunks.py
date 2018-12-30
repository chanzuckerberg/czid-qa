#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import os
import json
import threading
from util import smart_ls, check_output


EXIT_SUCCESS = 0
EXIT_DOWNLOAD_ERRORS = 101
CONCURRENT_DOWNLOADS = 8
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


def download(command, failed_downloads, downloader_license=threading.Semaphore(CONCURRENT_DOWNLOADS), lock=threading.RLock()):
    with downloader_license:
        try:
            check_output(command)
        except:
            with lock:
                failed_downloads[command] = True
            raise


def main(argv):
    project_path = parse_project_path(argv)
    print(f"Scoring project {project_path}.")
    GSNAP_M8_PREFIX = "multihit-gsnap-out-"
    GSNAP_FA_PREFIX = "gsnap_filter_1.fa-"
    GSNAP_ALT_PREFIX = "subsampled_1.fa-"
    project_failed_chunks = 0
    project_total_chunks = 0
    print("--------------------------------------------------------------------------------------------------------")
    failed_chunks = []
    for sample_results_path in sorted(find_samples_results(project_path)):
        sample_chunks = sorted(smart_ls(f"{sample_results_path}/chunks", missing_ok=True, quiet=True))
        if any(c.startswith(GSNAP_ALT_PREFIX) for c in sample_chunks):
            GSNAP_INPUT_PREFIX = GSNAP_ALT_PREFIX
        else:
            GSNAP_INPUT_PREFIX = GSNAP_FA_PREFIX
        read_1_chunk_ids = set(
            drop(GSNAP_INPUT_PREFIX, c, "")
            for c in sample_chunks
            if c.startswith(GSNAP_INPUT_PREFIX)
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
            for failed_id in read_1_chunk_ids ^ gsnap_success_ids:
                sample_id = sample_results_path.split("/results/", 1)[0].rsplit("/", 1)[1]
                failed_chunks.append({
                    's3_path': f"{sample_results_path}/chunks/{GSNAP_INPUT_PREFIX}{failed_id}",
                    'suitable_local_name': f"sample-{sample_id}-{GSNAP_INPUT_PREFIX}{failed_id}"
                })
    percent_failed = 100.0 * project_failed_chunks / project_total_chunks
    print("--------------------------------------------------------------------------------------------------------")
    print(f"Found {project_failed_chunks} failed of {project_total_chunks} total gsnap chunks ({percent_failed:3.0f}% failure rate) under project {project_path}.")
    failed_chunks = sorted(failed_chunks, key=lambda d: d['s3_path'])
    assert len(failed_chunks) == project_failed_chunks
    #print(json.dumps(failed_chunks, indent=4))
    threads = []
    failed_downloads = {}
    if len(argv) > 2 and argv[2].lower().strip("-") == "download":
        for fc in failed_chunks:
            command = f"aws s3 cp --only-show-errors {fc['s3_path']} {fc['suitable_local_name']}"
            t = threading.Thread(target=download, args=[command, failed_downloads])
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    if failed_downloads:
        print("ERROR:  {len(failed_downloads)} downloads failed.")
        return EXIT_DOWNLOAD_ERRORS
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        exitcode = main(sys.argv)
    except:
        print("USAGE:  See https://github.com/chanzuckerberg/idseq-qa/blob/master/README.md")
        raise
    os.sys.exit(exitcode)
