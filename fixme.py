#!/usr/bin/env python3

# this is a script to find fixmes on closed issues in rust
# It requires python 3, PyGithub, and a checkout of rust.
# This is used in the metabug https://github.com/rust-lang/rust/issues/44366

import os
import sys
import getpass
import logging
from os.path import join
import re
import subprocess
from github import Github

logging.basicConfig()
logger = logging.getLogger("fixme")
logger.setLevel("ERROR")

def collectFixmes(fixme_path):
    with open(fixme_path, 'w') as target:
        for root, dirs, files in os.walk(rust_path):
            for file_name in (join(root, name) for name in files):
                try:
                    for entry in createEntries(file_name):
                        target.write(entry)
                except UnicodeDecodeError:
                    logger.warning("could not decode {file_name} as UTF-8, skipping".format(file_name=file_name))

def createEntries(file_name):
    with open(file_name, 'r', encoding='utf-8') as source:
        for num, line in enumerate(source):
            match = re.search("FIXME.*?(\d{4,6})", line)
            if match:
                try:
                    issue = repo.get_issue(int(match.group(1)))
                    if issue.state == "closed":
                        code_url = "https://github.com/rust-lang/rust/blob/{revision}/{filename}#L{number}".format(revision=revision, filename=file_name.replace("\\", "/")[5:], number=str(num + 1))
                        issue_url = "https://github.com/rust-lang/rust/issues/{fixme}".format(fixme=match.group(1))
                        yield """
* [ ] ``` {line} ```
[code]({code_url}) -> [issue]({issue_url})
""".format(line=line.strip(), code_url=code_url, issue_url=issue_url)
                except:
                    logger.warning("""failed to obtain issue for {issue_num}.
line: {line}
source: {file_name}:{num}""".format(issue_num=match.group(1),
                        line=line,
                        file_name=file_name,
                        num=str(num + 1)))

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

gh = Github(username, password)
repo = gh.get_repo("rust-lang/rust")
rust_path = "rust/src"
fixme_path = "fixme.md"
revision = subprocess.check_output(["git", "rev-parse",  "--verify", "HEAD"], cwd='rust/src').strip().decode()

try:
    collectFixmes(fixme_path)
except (KeyboardInterrupt, SystemExit):
    logger.warning("collection of fixmes interrupted, intermediary file can be found in {path}".format(path=fixme_path))
    quit()
