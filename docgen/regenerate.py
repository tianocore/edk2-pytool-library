# @file regenerate.py
# Regenerates the documentation for this repo
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import generate
import sys
from xml.etree import ElementTree
from urllib.request import urlopen
import re
import subprocess


def scrape_links(dist, simple_index='https://pypi.org/simple/'):
    with urlopen(simple_index + dist + '/') as f:
        tree = ElementTree.parse(f)
    return [a.text for a in tree.iter('a')]


def run_pip_install(module, version, verbose=False):
    cmd = f"pip install {module}=={version} --force-reinstall"
    stdout = sys.stdout if verbose else subprocess.PIPE
    stderr = sys.stderr if verbose else subprocess.STDOUT
    c = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=True)
    c.wait()
    if c.returncode != 0:
        print(f"Failed to install {module}@{version}")
        sys.exit(1)


if __name__ == "__main__":
    module_name = "edk2-pytool-library"
    module = "edk2toollib"
    links = scrape_links(module_name)
    versions = set()
    version_reg = re.compile(r'(\d+(\.\d+)+)')

    for link in links:
        match = version_reg.search(link)
        if match is None:
            continue
        versions.add(match.group(0))
    for version in versions:
        try:
            print(f"Deploying {version}")
            run_pip_install(module_name, version)
            options = {}
            options["module"] = module
            options["deploy"] = True
            generate.main()
        except Exception as e:
            print(e)
            print("Failed to deploy")
