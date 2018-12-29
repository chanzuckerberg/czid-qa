#!/usr/bin/env python3

import sys
assert sys.version_info >= (3, 6), "Please run this script with Python version >= 3.6."

import subprocess


def check_output(command, quiet=False):
    # Assuming python >= 3.6
    shell = isinstance(command, str)
    if not quiet:
        command_str = command if shell else " ".join(command)
        print(repr(command_str))
    return subprocess.check_output(command, shell=shell).decode('utf-8')


def smart_ls(pdir, missing_ok=True, memory=None, quiet=False):
    "Return a list of files in pdir.  This pdir can be local or in s3.  If memory dict provided, use it to memoize.  If missing_ok=True, swallow errors (default)."
    result = memory.get(pdir) if memory else None
    if result == None:
        try:
            if pdir.startswith("s3"):
                s3_dir = pdir
                if not s3_dir.endswith("/"):
                    s3_dir += "/"
                output = check_output(["aws", "s3", "ls", s3_dir], quiet=quiet)
                rows = output.strip().split('\n')
                result = [r.split()[-1] for r in rows]
            else:
                output = check_output(["ls", pdir], quiet=quiet)
                result = output.strip().split('\n')
        except Exception as e:
            msg = f"Could not read directory: {pdir}"
            if missing_ok and isinstance(e, subprocess.CalledProcessError):
                print(f"INFO: {msg}")
                result = []
            else:
                print(f"ERROR: {msg}")
                raise
        if memory != None:
            memory[pdir] = result
    return result


if __name__ == "__main__":
    print(check_output("echo Hello world!").strip())
