#!/usr/bin/env python3
"""Verify the unsigned IPA this workflow produced.

An unsigned archive can "succeed" while being useless, so this checks the things
that actually decide whether the IPA installs and runs:

  * the guest image is in the bundle, is a plausible size, and its bytes match
    the sha256 the app compares at launch (a truncated copy phase would ship an
    app that boots into an empty guest);
  * the app binary is an arm64 iOS executable (not a macOS or simulator one);
  * the bundle carries the identity, version and minimum OS we expect;
  * nothing was signed — an unsigned IPA must have no _CodeSignature and no
    embedded.mobileprovision, otherwise a re-signing tool gets confused.

Usage: verify-ipa.py path/to/DSH-unsigned.ipa
"""
import hashlib
import plistlib
import struct
import sys
import zipfile

IPA = sys.argv[1] if len(sys.argv) > 1 else 'build/DSH-unsigned.ipa'
APP = 'Payload/DSH.app/'

CPU_ARCH_ABI64 = 0x01000000
CPU_TYPE_ARM64 = CPU_ARCH_ABI64 | 12
MH_EXECUTE = 2
PLATFORMS = {1: 'macOS', 2: 'iOS', 3: 'tvOS', 4: 'watchOS', 6: 'macCatalyst', 7: 'iOS-simulator'}
LC_BUILD_VERSION = 0x32

EXPECTED_BUNDLE_ID = 'com.xnuapp.dsh'
EXPECTED_MIN_OS = '16.0'

problems = []
report = []


def fail(message):
    problems.append(message)


def ok(message):
    report.append('ok   ' + message)


def sha256_member(archive, name):
    digest = hashlib.sha256()
    size = 0
    with archive.open(name) as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def macho_summary(header):
    if len(header) < 32:
        return None, 'truncated (%d bytes, not a Mach-O header)' % len(header)
    magic, cputype, _cpusubtype, filetype = struct.unpack_from('<4I', header, 0)
    if magic != 0xFEEDFACF:
        return None, 'unknown Mach-O magic 0x%08X' % magic
    ncmds, sizeofcmds = struct.unpack_from('<2I', header, 16)
    info = {'cputype': cputype, 'filetype': filetype, 'platform': None, 'minos': None}
    offset = 32
    for _ in range(ncmds):
        if offset + 8 > len(header):
            break
        cmd, cmdsize = struct.unpack_from('<2I', header, offset)
        if cmd == LC_BUILD_VERSION and offset + 24 <= len(header):
            platform, minos, _sdk = struct.unpack_from('<3I', header, offset + 8)
            info['platform'] = PLATFORMS.get(platform, platform)
            info['minos'] = '%d.%d' % (minos >> 16, (minos >> 8) & 0xFF)
        offset += cmdsize
    return info, None


with zipfile.ZipFile(IPA) as archive:
    names = archive.namelist()
    index = {name: info for name, info in ((i.filename, i) for i in archive.infolist())}

    for required in (APP + 'Info.plist', APP + 'DSH', APP + 'root.tar.gz', APP + 'root.tar.gz.sha256'):
        if required not in names:
            fail('%s is missing from the IPA' % required)
    if problems:
        print('\n'.join('::error::' + p for p in problems))
        sys.exit(1)

    info = plistlib.loads(archive.read(APP + 'Info.plist'))
    identity = (info.get('CFBundleIdentifier'), info.get('CFBundleShortVersionString'),
                info.get('CFBundleVersion'), info.get('MinimumOSVersion'),
                info.get('CFBundleDisplayName'))
    ok('bundle %s · %s (%s) · minimum iOS %s · “%s”' % identity)
    if identity[0] != EXPECTED_BUNDLE_ID:
        fail('bundle id is %r, expected %r' % (identity[0], EXPECTED_BUNDLE_ID))
    if identity[3] != EXPECTED_MIN_OS:
        fail('MinimumOSVersion is %r, expected %r' % (identity[3], EXPECTED_MIN_OS))

    expected_sha = archive.read(APP + 'root.tar.gz.sha256').decode().strip()
    actual_sha, size = sha256_member(archive, APP + 'root.tar.gz')
    ok('guest image %.1f MB, sha256 %s…' % (size / 1e6, actual_sha[:16]))
    if size < 40e6:
        fail('the guest image is %.1f MB — far smaller than the ~81 MB image, the copy is truncated' % (size / 1e6))
    if actual_sha != expected_sha:
        fail('root.tar.gz does not match the sha256 shipped beside it (%s vs %s)' % (actual_sha, expected_sha))

    binary, error = macho_summary(archive.read(APP + 'DSH'))
    if binary is None:
        fail('the app binary: %s' % error)
    else:
        cputype, filetype = binary['cputype'], binary['filetype']
        platform, minos = binary['platform'], binary['minos']
        ok('app binary: %s, %s, platform %s %s' % (
            'arm64' if cputype == CPU_TYPE_ARM64 else 'cputype 0x%08X' % cputype,
            'executable' if filetype == MH_EXECUTE else 'filetype %d' % filetype, platform, minos))
        if cputype != CPU_TYPE_ARM64:
            fail('the app binary is not arm64 — it cannot run on a device')
        if filetype != MH_EXECUTE:
            fail('the app binary is not an executable')
        if platform != 'iOS':
            fail('the app binary was built for %s, not iOS' % platform)

    signed = [n for n in names if '_CodeSignature' in n or n.endswith('embedded.mobileprovision')]
    if signed:
        fail('the IPA is signed (%s) — it was supposed to come out unsigned' % ', '.join(signed[:3]))
    else:
        ok('unsigned: no _CodeSignature, no embedded provisioning profile')

    total = sum(index[name].file_size for name in names)
    ok('%d entries, ~%.1f MB uncompressed' % (len(names), total / 1e6))

print('## IPA verification')
for line in report:
    print('- ' + line)
if problems:
    for problem in problems:
        print('::error::%s' % problem)
    sys.exit(1)
print('\nall checks passed')
