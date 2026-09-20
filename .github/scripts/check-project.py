#!/usr/bin/env python3
"""Sanity-check the Xcode project before spending build minutes on it.

DSH.xcodeproj is generated (scripts/gen-xcode-project.rb) and committed, so the
one failure mode worth catching early is a project that has drifted from the
sources: a new app/*.m that nobody added to the target compiles only as an
undefined symbol several minutes into the build, and a missing meson phase looks
like a normal link error at the very end.

Usage: check-project.py [path/to/project.pbxproj]
"""
import glob
import os
import re
import sys

PBXPROJ = sys.argv[1] if len(sys.argv) > 1 else 'DSH.xcodeproj/project.pbxproj'
# Run from the repository root (the workflow does); fall back to the project's
# parent directory if the path was given from somewhere else.
ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'app')):
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(PBXPROJ)))

with open(PBXPROJ, errors='ignore') as fh:
    text = fh.read()

problems = []
notes = []

for pattern, what in (('app/*.m', 'source'), ('app/*.h', 'header')):
    for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
        name = os.path.basename(path)
        if name not in text:
            problems.append('app/%s (a %s file) is missing from %s' % (name, what, PBXPROJ))

for phase in ('Build Meson (iSH-ARM64)', 'Copy DSH Root', 'Generate APK Repositories File',
              'Compile hterm JavaScript'):
    if phase not in text:
        problems.append('build phase %r is missing — regenerate with `make project`' % phase)

for needed, why in (
        ('deps/libarchive.xcodeproj', 'libarchive is linked from the vendored project'),
        ('RootfsPatch.bundle', 'the guest fetch() polyfill is bundled as a resource'),
        ('DSH_ROOTFS_TARBALL', 'the guest image is copied into the app bundle'),
):
    if needed not in text:
        problems.append('%s is missing (%s)' % (needed, why))

sources = len(re.findall(r'in Sources \*/', text))
notes.append('%d source files referenced' % sources)
if sources < 80:
    problems.append('only %d source files referenced — the project looks truncated' % sources)

print('project check: %s' % (', '.join(notes)))
for problem in problems:
    print('::error::%s' % problem)
if problems:
    sys.exit(1)
print('project check ok')
