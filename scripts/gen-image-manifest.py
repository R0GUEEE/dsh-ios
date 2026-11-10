#!/usr/bin/env python3
"""Describe the guest image to the plugins that run inside it.

The manifest is read by `dsh-ios` (see rootfs/overlay/usr/local/lib/dsh-plugins)
to answer three questions without hardcoding any of them:

  dshVersion  the pinned @deepseek-ai/dsh this image ships — the runtime a
              plugin manager must judge compatibility against, *not* whatever
              a pnpm-installed profile next to it declares
  plugins     package names of the dsh plugins actually present in the pinned
              tree (anything with a cordis.patch.yml or a `dsh` field), i.e.
              what a profile may mount without fetching from a registry
  tools       every model-facing tool the pinned tree can register, gathered
              from the `dsh-tool-*` packages, so a settings switch that turns
              plugin tools off still leaves the image's own tools alone

Derived from rootfs/staging/package-lock.json, which build-rootfs.sh installs
and then pins. Run by scripts/build-rootfs.sh; safe to run by hand:

    scripts/gen-image-manifest.py [path/to/package-lock.json] [out.json]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "rootfs", "staging", "package-lock.json")
OUT = os.path.join(ROOT, "rootfs", "overlay", "usr", "local", "share", "dsh", "image.json")

# Packages that are the harness itself rather than optional plugins: they ship
# in the pinned tree but a profile mounts them through a bundle, never alone.
NOT_A_PLUGIN = {"@deepseek-ai/dsh", "@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app",
                "@deepseek-ai/dsh-headless", "@deepseek-ai/dsh-typert-registry"}

# Plugins this repository ships itself, listed in rootfs/overlay/.../home.patch.yml.
# They are not registry packages, so the lockfile cannot name them.
OVERLAY_PLUGINS = ["dsh-host-bridge", "dsh-ios"]


def package_dir(packages, name):
    return packages.get("node_modules/" + name)


def main(lock_path, out_path):
    with open(lock_path, encoding="utf-8") as f:
        lock = json.load(f)
    packages = lock.get("packages", {})

    dsh = package_dir(packages, "@deepseek-ai/dsh")
    if not dsh:
        sys.exit(f"no @deepseek-ai/dsh in {lock_path}")
    version = dsh["version"]

    # The pinned tree an app image installs: dsh plus every direct dependency it
    # declares. Anything deeper (transitive) is a library, not a mountable plugin.
    surface = ["@deepseek-ai/dsh"]
    for dep in sorted((dsh.get("dependencies") or {})):
        if dep.startswith("@deepseek-ai/") and package_dir(packages, dep):
            surface.append(dep)

    plugins = [n for n in surface if n not in NOT_A_PLUGIN]
    # The image's own overlay plugins are part of the composition too, and the
    # in-guest guard needs to know they are mounted (it refuses to let anything
    # else answer to a bridge tool name).
    plugins += [p for p in OVERLAY_PLUGINS if p not in plugins]
    # Package name → model-facing tool names. Not 1:1: dsh-tool-fs registers
    # read/write/edit/read_image and dsh-tool-web registers web_search/
    # web_fetch, while a few packages (subagent, workflow) name their tool from
    # configuration. The mapping comes from the pinned packages' definitions,
    # not from guessing at the package name.
    TOOL_PACKAGES = {
        "@deepseek-ai/dsh-tool-ask-user": ["ask_user_question"],
        "@deepseek-ai/dsh-tool-bash": ["bash"],
        "@deepseek-ai/dsh-tool-bash-persistent": ["bash"],
        "@deepseek-ai/dsh-tool-cordis": [
            "cordis_define", "cordis_undefine", "cordis_inspect_list",
            "cordis_inspect_query", "cordis_inspect_self", "cordis_run", "cordis_stop",
        ],
        "@deepseek-ai/dsh-tool-fs": ["read", "write", "edit", "read_image"],
        "@deepseek-ai/dsh-tool-fs-search": ["glob", "grep"],
        "@deepseek-ai/dsh-tool-goal": ["create_goal", "get_goal", "update_goal"],
        "@deepseek-ai/dsh-tool-jobs": ["job_list", "job_output", "job_kill"],
        "@deepseek-ai/dsh-tool-pwsh": ["pwsh"],
        "@deepseek-ai/dsh-tool-ralph": ["ralph"],
        "@deepseek-ai/dsh-tool-skill": ["skill"],
        "@deepseek-ai/dsh-tool-str-replace-editor": ["str_replace_editor"],
        "@deepseek-ai/dsh-tool-subagent": ["subagent"],
        "@deepseek-ai/dsh-tool-subagent-control": ["send_message", "interrupt_agent"],
        "@deepseek-ai/dsh-tool-subagent-report": ["report"],
        "@deepseek-ai/dsh-tool-todo": ["todo_write"],
        "@deepseek-ai/dsh-tool-web": ["web_search", "web_fetch"],
        "@deepseek-ai/dsh-tool-workflow": ["workflow"],
    }

    tools = sorted({t for pkg in surface for t in TOOL_PACKAGES.get(pkg, [])})

    manifest = {
        "schema": 1,
        "dshVersion": version,
        "node": "22",
        "platform": {"host": "ios", "runtime": "ish-arm64", "guest": "alpine", "arch": "aarch64"},
        "plugins": plugins,
        "tools": tools,
        "bridgeTools": [
            "device_info", "device_power", "calendar_query", "calendar_create_event",
            "reminders_query", "reminders_create", "health_query", "location_query",
            "contacts_search", "notify", "file_import", "file_export", "photo_import",
            "share", "shortcut_run",
        ],
        # Everything in `tools` plus the bridge, which is what the image's own
        # plugin set can offer the model before the user's profile adds anything.
        "shippedTools": sorted(set(tools) | {
            "device_info", "device_power", "calendar_query", "calendar_create_event",
            "reminders_query", "reminders_create", "health_query", "location_query",
            "contacts_search", "notify", "file_import", "file_export", "photo_import",
            "share", "shortcut_run",
        }),
        "packages": sorted(surface),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)
        f.write("\n")
    print(f"{out_path}: dsh {version}, {len(plugins)} plugin packages, {len(tools)} tools")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else LOCK,
         sys.argv[2] if len(sys.argv) > 2 else OUT)
