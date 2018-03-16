#!/usr/bin/env python3


# this is a half baked and first draft script to find fixmes on closed issues in rust
# It requires python 3, github3, and a checkout of rust.
# This is used in the metabug https://github.com/rust-lang/rust/issues/44366


# If you want to improve it, please be in touch. I'd love to help, or see what you accomplish!


import os
import sys
import getpass
import logging
from os.path import join
import re
import subprocess
from github3 import GitHub

logging.basicConfig()
logger = logging.getLogger("fixme")
logger.setLevel("ERROR")

def collectFixmes(gh, rust_path, fixme_path):
    with open(fixme_path, 'w') as target:
        target.write("This is the output of a half baked and first draft script to find fixmes on closed issues in rust.\n")
        for root, dirs, files in os.walk(rust_path):
            for file_name in (join(root, name) for name in files):
                try:
                    for entry in createEntries(gh, file_name):
                        target.write(entry)
                except UnicodeDecodeError:
                    logger.warning("could not decode {file_name} as UTF-8, skipping".format(file_name=file_name))

def createEntries(gh, file_name):
    with open(file_name, 'r', encoding='utf-8') as source:
        for num, line in enumerate(source):
            match = re.search("FIXME.*?(\d{4,6})", line)
            if match:
                try:
                    issue = gh.issue("rust-lang", "rust", match.group(1))
                    closed = issue.is_closed()
                except AttributeError:
                    logger.warning("""failed to obtain issue for {issue_num}.
line: {line}
source: {file_name}:{num}""".format(issue_num=match.group(1),
                        line=line,
                        file_name=file_name,
                        num=str(num + 1)))
                else:
                    if closed:
                        logger.info(issue.ratelimit_remaining)
                        code_url = "https://github.com/rust-lang/rust/blob/{sha}/{filename}#L{number}".format(sha=sha, filename=file_name.replace("\\", "/")[5:], number=str(num + 1))
                        issue_url = "https://github.com/rust-lang/rust/issues/{fixme}".format(fixme=match.group(1))
                        yield """
``` {line} ```
[code]({code_url}) -> [issue]({issue_url})
""".format(line=line.strip(), code_url=code_url, issue_url=issue_url)


if len(sys.argv) >= 2:
    username = sys.argv[1]
else:
    logger.error("username argument missing")
    quit()

try:
    password = getpass.getpass()
except (KeyboardInterrupt, SystemExit):
    logger.error("password input cancelled, Aborting")
    quit()

gh = GitHub(username, password)
rust_path = "rust/src"
fixme_path = "fixme.md"
sha = subprocess.check_output(["git", "rev-parse",  "--verify", "HEAD"], cwd='rust/src').strip().decode()
ratelimit_remaining = gh.issue("rust-lang", "rust", "1").ratelimit_remaining

if ratelimit_remaining < 2000:
   logger.error("we do not seem to have enough ratelimit remaining to run. Aborting.")
   quit()

try:
    collectFixmes(gh, rust_path, fixme_path)
except (KeyboardInterrupt, SystemExit):
    logger.warning("collection of fixmes interrupted, intermediary file can be found in {path}".format(path=fixme_path))
    quit()
