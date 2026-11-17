#!/usr/bin/env python3
"""Report whether a Maven Surefire/Failsafe test case failed or errored."""
import os
from pathlib import Path
import xml.etree.ElementTree as ET

failed_reports = []
reports_scanned = 0

for report in Path(".").rglob("TEST-*.xml"):
    if report.parent.name not in ("surefire-reports", "failsafe-reports"):
        continue
    reports_scanned += 1
    try:
        root = ET.parse(report).getroot()
    except (ET.ParseError, OSError) as exc:
        print(f"Could not parse test report {report}: {exc}")
        continue
    suites = [root] if root.tag.split("}")[-1] == "testsuite" else [
        node for node in root.iter()
        if node.tag.split("}")[-1] == "testsuite"
    ]
    if any(
        int(suite.get("failures", "0")) > 0
        or int(suite.get("errors", "0")) > 0
        for suite in suites
    ):
        failed_reports.append(str(report))

test_failed = bool(failed_reports)
print(f"Inspected {reports_scanned} Maven test reports.")
if test_failed:
    for report in failed_reports:
        print(f"Test failure or error reported in: {report}")
else:
    print("No failed Maven test case found; Rickroll will not run.")

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
    output.write(f"test_failed={str(test_failed).lower()}\n")
