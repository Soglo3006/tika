#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Report whether Maven Surefire/Failsafe produced failed test cases.

Read Maven's plain-text test summaries; no XML parser or extra dependency needed.
"""
import os
from pathlib import Path
import re

summary = re.compile(
    r"Tests run:\s*\d+,\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)"
)
failed_reports = []
reports_scanned = 0

for report in Path(".").rglob("*.txt"):
    if report.parent.name not in ("surefire-reports", "failsafe-reports"):
        continue
    reports_scanned += 1
    try:
        content = report.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Could not read test report {report}: {exc}")
        continue
    if any(
        int(failures) > 0 or int(errors) > 0
        for failures, errors in summary.findall(content)
    ):
        failed_reports.append(str(report))

test_failed = bool(failed_reports)
print(f"Inspected {reports_scanned} Maven test summaries.")
if test_failed:
    for report in failed_reports:
        print(f"Test failure or error reported in: {report}")
else:
    print("No failed Maven test case found; Rickroll will not run.")

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
    output.write(f"test_failed={str(test_failed).lower()}\n")
