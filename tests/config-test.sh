#!/usr/bin/env bash
# Configuration gate for the DSH guest profile.
#
# The parts of tests/rootfs-test.sh that describe the guest *configuration* —
# the cordis patch layers, the skills roots, the MCP loader, the image manifest
# — do not need the emulator, the guest image, or macOS. They need node and the
# pinned dsh tree. This script runs exactly those, so the configuration has a
# gate that any Linux or macOS machine can run in seconds.
#
# It deliberately does NOT replace tests/rootfs-test.sh: everything that boots
# the guest, drives an agent turn, or exercises the bridge still needs the
# emulator (an AArch64 host, in practice a Mac).
#
# Usage:
#   tests/config-test.sh [<path-to-installed-dsh-tree>]
#
# The optional argument is a directory containing @deepseek-ai/dsh (the guest's
# /usr/local/lib/node_modules, or a `npm ci` of rootfs/staging). Without it the
# script installs the pinned tree into a temporary directory first.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
WORK="${WORK:-$(mktemp -d)}"
trap 'rm -rf "$WORK"' EXIT

pass=0; fail=0
ok()  { pass=$((pass+1)); printf '  \033[32mPASS\033[0m %s\n' "$*"; }
bad() { fail=$((fail+1)); printf '  \033[31mFAIL\033[0m %s\n' "$*"; }
# check <name> <command...>: no eval, so a value can never become a command
check() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name"; fi; }

command -v node >/dev/null || { echo "node is required"; exit 2; }

NODE_MODULES="${1:-}"
if [ -z "$NODE_MODULES" ]; then
    echo "== installing the pinned dsh tree (rootfs/staging)"
    mkdir -p "$WORK/tree"
    cp "$ROOT/rootfs/staging/package.json" "$WORK/tree/"
    [ -f "$ROOT/rootfs/staging/package-lock.json" ] && cp "$ROOT/rootfs/staging/package-lock.json" "$WORK/tree/"
    ( cd "$WORK/tree" && npm ci --no-audit --no-fund --ignore-scripts --loglevel=error ) || {
        echo "npm ci failed; pass a prebuilt tree instead"; exit 2; }
    NODE_MODULES="$WORK/tree/node_modules"
fi

DSH_BIN="$NODE_MODULES/@deepseek-ai/dsh/lib/bin.js"
[ -f "$DSH_BIN" ] || { echo "no dsh at $DSH_BIN"; exit 2; }

# Compose the profile exactly as dsh-serve installs it on a device: the home
# layer over every profile, and the web layer over that.
echo "== compose the image's patch layers"
mkdir -p "$WORK/home/.dsh/profiles/web"
cp "$ROOT/rootfs/overlay/usr/local/share/dsh/home.patch.yml" "$WORK/home/.dsh/cordis.patch.yml"
cp "$ROOT/rootfs/overlay/usr/local/share/dsh/cordis.patch.yml" "$WORK/home/.dsh/profiles/web/cordis.patch.yml"
# The overlay names plugins by their installed path; point it at this checkout.
sed -i.bak "s|/usr/local/lib/dsh-plugins|$ROOT/rootfs/overlay/usr/local/lib/dsh-plugins|g" \
    "$WORK/home/.dsh/cordis.patch.yml"

HOME="$WORK/home" DSH_HOME="$WORK/home/.dsh" \
    node --expose-internals "$DSH_BIN" --profile web --dump-config > "$WORK/config.yml" 2>"$WORK/config.err"
check "profile composes" test -s "$WORK/config.yml"
CONFIG="$WORK/config.yml"

echo "== the image's patch layers reach the composition"
check "sandbox-policy is danger-full-access" sh -c "grep -A2 'id: sandbox-policy' '$CONFIG' | grep -q danger-full-access"
check "ios-platform row composed"            grep -q 'id: ios-platform' "$CONFIG"
check "ios-mcp row composed"                 grep -q 'id: ios-mcp' "$CONFIG"
check "host-bridge row composed"             grep -q 'id: host-bridge' "$CONFIG"

echo "== skills roots"
check "skill-filesystem carries a bundled root" grep -A12 'id: skill-filesystem' "$CONFIG" | grep -q 'bundledSkillDir'
check "bundled root is the image's directory"   grep -A12 'id: skill-filesystem' "$CONFIG" | grep -q '/usr/local/share/dsh/skills'
check "skill watching polls"                     grep -A12 'id: skill-filesystem' "$CONFIG" | grep -q 'watchUsePolling: true'
check "the shipped skill satisfies the name rule" grep -q '^name: dsh-ios-platform$' "$ROOT/rootfs/overlay/usr/local/share/dsh/skills/dsh-ios-platform/SKILL.md"
check "the shipped skill has a description"       grep -q '^description: .' "$ROOT/rootfs/overlay/usr/local/share/dsh/skills/dsh-ios-platform/SKILL.md"

echo "== MCP"
MCP="$ROOT/rootfs/overlay/usr/local/share/dsh/mcp.example.json"
check "an mcp example ships" test -f "$MCP"
check "the mcp example parses and declares no servers" \
    node -e "const c=require(process.argv[1]); process.exit(c.servers && !Object.keys(c.servers).length ? 0 : 1)" "$MCP"

echo "== image manifest"
MANIFEST="$ROOT/rootfs/overlay/usr/local/share/dsh/image.json"
check "the manifest ships" test -f "$MANIFEST"
check "the manifest names the pinned dsh"  grep -q '"dshVersion"' "$MANIFEST"
check "the manifest lists the host bridge" grep -q 'dsh-host-bridge' "$MANIFEST"
check "the manifest lists the runtime layer" grep -q 'dsh-ios' "$MANIFEST"

echo
echo "passed=$pass failed=$fail"
[ "$fail" = 0 ]
