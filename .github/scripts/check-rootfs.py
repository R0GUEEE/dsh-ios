#!/usr/bin/env python3
"""Verify build/root.tar.gz is a complete guest image.

The guest build runs inside the emulator, and the emulator's exit status does
not carry the guest shell's: a phase that fails before installing anything still
produces a root.tar.gz of a plausible size, and the app then boots a guest with
no node in it. scripts/build-rootfs.sh checks the fakefs after every phase; this
checks the exported tarball, which is what actually ships inside the app.

Usage: check-rootfs.py [build/root.tar.gz] [rootfs/staging/package.json]
"""
import json
import os
import sys
import tarfile

TARBALL = sys.argv[1] if len(sys.argv) > 1 else 'build/root.tar.gz'
STAGING = sys.argv[2] if len(sys.argv) > 2 else 'rootfs/staging/package.json'
DSH_VERSION = None
if os.path.exists(STAGING):
    with open(STAGING) as handle:
        DSH_VERSION = json.load(handle).get('dependencies', {}).get('@deepseek-ai/dsh')

REQUIRED = [
    ('/bin/busybox', 'the guest has a shell'),
    ('/lib/libc.musl-aarch64.so.1', 'the guest is an aarch64 musl root'),
    ('/usr/bin/node', 'node was installed by apk'),
    ('/usr/bin/npm', 'npm was installed by apk'),
    ('/usr/local/lib/node_modules/@deepseek-ai/dsh/lib/bin.js', 'the dsh entry point'),
    ('/usr/local/lib/node_modules/@deepseek-ai/dsh/package.json', 'the dsh package'),
    ('/usr/local/lib/node_modules/node-pty/build/Release/pty.node', 'node-pty was rebuilt for musl'),
    ('/usr/local/lib/dsh-plugins/dsh-host-bridge/index.js', 'the iOS host bridge plugin'),
    ('/usr/local/bin/dsh-serve', 'the harness entry point'),
    ('/usr/local/bin/dsh-selftest', 'the guest self test'),
    ('/usr/local/share/dsh/cordis.patch.yml', 'the dsh profile patch'),
    ('/usr/local/share/dsh/home.patch.yml', 'the home-level profile layer'),
    ('/lib/fetch-polyfill.js', 'the streaming fetch() polyfill'),
    ('/root/.dsh/profiles/web/cordis.patch.yml', 'the pre-scaffolded web profile'),
    ('/root/workspace', 'the guest workspace'),
    ('/etc/alpine-release', 'the Alpine release marker'),
]

problems = []
report = []

if not os.path.exists(TARBALL):
    print('::error::%s does not exist' % TARBALL)
    sys.exit(1)

size = os.path.getsize(TARBALL)
report.append('%.1f MB' % (size / 1e6))
if size < 30e6:
    problems.append('the tarball is only %.1f MB — the guest build cannot have completed' % (size / 1e6))

with tarfile.open(TARBALL, 'r:gz') as archive:
    members = archive.getmembers()
    by_name = {}
    for member in members:
        by_name.setdefault(member.name.lstrip('./'), member)

    for path, why in REQUIRED:
        member = by_name.get(path.lstrip('/'))
        if member is None:
            problems.append('%s is missing (%s)' % (path, why))
        elif member.isfile() and member.size == 0:
            problems.append('%s is empty (%s)' % (path, why))

    # A file that must be executable: tar records the mode.
    for path in ('/usr/bin/node', '/usr/local/bin/dsh-serve', '/usr/local/bin/dsh'):
        member = by_name.get(path.lstrip('/'))
        if member is not None and not (member.mode & 0o111):
            problems.append('%s is not executable (mode %o)' % (path, member.mode))

    modules = [n for n in by_name if n.startswith('usr/local/lib/node_modules/') and n.count('/') == 4]
    report.append('%d node_modules entries' % len(modules))
    if len(modules) < 200:
        problems.append('only %d top-level node_modules entries — the payload looks truncated' % len(modules))

    node_pty = by_name.get('usr/local/lib/node_modules/node-pty/build/Release/pty.node')
    if node_pty is not None:
        report.append('node-pty binary %.0f KB' % (node_pty.size / 1024))

    release = by_name.get('etc/alpine-release')
    if release is not None:
        version = archive.extractfile(release).read().decode().strip()
        report.append('Alpine %s' % version)
        if not version.startswith('3.21'):
            problems.append('Alpine %s — expected 3.21' % version)

    dsh_pkg = by_name.get('usr/local/lib/node_modules/@deepseek-ai/dsh/package.json')
    if dsh_pkg is not None:
        version = json.load(archive.extractfile(dsh_pkg)).get('version')
        report.append('dsh %s' % version)
        if DSH_VERSION and version != DSH_VERSION:
            problems.append('dsh %s is in the image but rootfs/staging pins %s' % (version, DSH_VERSION))

    npm_pkg = by_name.get('usr/lib/node_modules/npm/package.json')
    if npm_pkg is not None:
        report.append('npm %s' % json.load(archive.extractfile(npm_pkg)).get('version'))

    leftovers = [p for p in ('usr/bin/python3', 'usr/bin/make', 'usr/bin/g++') if p in by_name]
    report.append('build tooling removed' if not leftovers else 'build tooling still present: %s' % ', '.join(leftovers))

print('## Guest image (%s)' % TARBALL)
for line in report:
    print('- ' + line)
if problems:
    for problem in problems:
        print('::error::%s' % problem)
    sys.exit(1)
print('\nguest image ok')
