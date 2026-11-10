/**
 * dsh-ios — the app's plugin-platform layer inside the guest.
 *
 * Two jobs, both about authority the agent must not be able to take back:
 *
 * 1. Runtime compatibility. A plugin manager decides whether a package may
 *    run on the *runtime*, not on the host OS. This guest's runtime is the
 *    pinned `dsh` tree at /usr/local/lib/node_modules, installed by the app
 *    image; a pnpm-installed profile next to it is not the runtime. The
 *    service published here answers with the pinned version, the platform
 *    facts, and the packages this emulator cannot host (no PowerShell, no
 *    tmux, no Landlock). Packages are exposed to `dsh plugin add` by the
 *    NODE_PATH set in `dsh-serve`, not by copying into the agent-writable
 *    profile directory.
 *
 * 2. The composition guard. The agent runs as root in the guest and owns
 *    `~/.dsh`, so it can edit the home and profile patch layers, rewrite the
 *    pinned tree, or run pnpm — and mount arbitrary Host code in-process.
 *    The app's promise is that every iOS capability passes the host bridge
 *    and its native gate. `ctx.tools.guard()` is the one monotonic gate every
 *    tool call passes, from any session and from PTC program calls, so the
 *    policy lives there rather than in a prompt or in a patch file the agent
 *    can rewrite.
 *
 * Neither job can throw at load: a profile that cannot use a service still
 * boots and still runs its tools.
 *
 * Policy inputs are read per call from the app's settings document
 * (`DSH_IOS_SETTINGS`, default /root/.dsh/ios.json, written by the app and
 * never by the agent) and from the image's own manifest
 * (`/usr/local/share/dsh/image.json`).
 *
 * @module dsh-ios
 */
import { readFileSync } from "node:fs";

export const name = "ios-platform";

/** The pinned tree, and the manifest the image builder leaves beside the overlay. */
const MANIFEST_FILE = process.env.DSH_IMAGE_MANIFEST ?? "/usr/local/share/dsh/image.json";
const SETTINGS_FILE = process.env.DSH_IOS_SETTINGS ?? "/root/.dsh/ios.json";

/**
 * Bridge tool names. A guest-side tool answering to one of these would
 * shadow the app's tool and route around the capability switch and the
 * native confirmation it exists behind.
 */
const BRIDGE_TOOLS = [
  "device_info", "device_power", "calendar_query", "calendar_create_event",
  "reminders_query", "reminders_create", "health_query", "location_query",
  "contacts_search", "notify", "file_import", "file_export", "photo_import",
  "share", "shortcut_run",
];

/** Engines a profile may mount that cannot work in this guest at all. */
const UNSUPPORTED_PACKAGES = {
  "dsh-pwsh-local": "PowerShell: the guest image ships no pwsh",
  "dsh-pwsh-sandbox": "PowerShell: the guest image ships no pwsh",
  "dsh-tool-pwsh": "PowerShell: the guest image ships no pwsh",
  "dsh-tmux-context": "tmux is not installed in the guest image",
  "dsh-sandbox-local": "the iSH kernel has neither Landlock nor bubblewrap (sandbox mode is danger-full-access)",
};

/** Program-mode tools that can start another agent loop or mount Host code. */
const LOOP_OR_UI_TOOLS = ["workflow", "cordis_run", "cordis_define", "subagent"];

/** The image's own tool set, from the manifest the build writes. */
function shippedTools() {
  const m = manifest();
  const list = Array.isArray(m?.shippedTools) ? m.shippedTools : [];
  return list.length ? new Set(list) : undefined;
}
function readJson(file) {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return undefined;
  }
}

function manifest() {
  const m = readJson(MANIFEST_FILE);
  return m && typeof m === "object" ? m : undefined;
}

function settings() {
  const s = readJson(SETTINGS_FILE);
  return s && typeof s === "object" ? s : {};
}

/** Semver-ish comparison good enough for `>=x.y.z` and exact pins. */
function compare(a, b) {
  const pa = a.split(/[.+-]/);
  const pb = b.split(/[.+-]/);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const x = pa[i] ?? "0";
    const y = pb[i] ?? "0";
    const nx = /^\d+$/.test(x);
    const ny = /^\d+$/.test(y);
    if (nx && ny) {
      if (Number(x) !== Number(y)) return Number(x) < Number(y) ? -1 : 1;
      continue;
    }
    if (x === y) continue;
    return x < y ? -1 : 1;
  }
  return 0;
}

function satisfies(range, version) {
  const want = String(range ?? "").trim();
  // An unreadable manifest means "this is not the app's image", not "anything
  // fits": a caller asking whether a package may run here must get a refusal it
  // can explain, not a silent yes from a missing file.
  if (!version) return want === "";
  if (!want) return true;
  return want.split("||").some((part) => {
    const r = part.trim();
    const floor = /^>=\s*(\S+)$/.exec(r);
    if (floor) return compare(version, floor[1]) >= 0;
    const exact = /^=\s*(\S+)$/.exec(r);
    if (exact) return compare(version, exact[1]) === 0;
    // A range this layer cannot interpret is not a refusal: the plugin manager
    // owns compatibility grammar, and refusing on a parse miss would be worse
    // than letting it decide.
    return true;
  });
}

export function apply(ctx) {
  const dshVersion = manifest()?.dshVersion ?? null;

  const runtime = {
    /** The pinned dsh the app image ships. */
    version: dshVersion,
    managed: dshVersion !== null,
    platform: {
      host: "ios",
      runtime: "ish-arm64",
      guest: "alpine",
      arch: "aarch64",
      sandbox: "danger-full-access",
    },
    settings,
    satisfies,
    unsupported: (pkg) => UNSUPPORTED_PACKAGES[pkg] ?? null,
  };
  ctx.provide("dshRuntime", runtime);

  const policy = () => {
    const s = settings();
    const denied = new Set(Array.isArray(s.denyTools) ? s.denyTools : []);
    for (const tool of Array.isArray(s.allowTools) ? s.allowTools : []) denied.delete(tool);
    return { denied, allowPlugins: s.allowPluginTools !== false, allowPtcShell: s.allowPtcShell === true };
  };

  const installed = () => new Set(Array.isArray(manifest()?.plugins) ? manifest().plugins : []);

  ctx.tools.guard((exec) => {
    const tool = typeof exec?.name === "string" ? exec.name : "";
    if (!tool) return undefined;
    const { denied, allowPlugins, allowPtcShell } = policy();

    if (denied.has(tool)) return `${tool} is switched off in DSH on iOS`;
    if (BRIDGE_TOOLS.includes(tool) && !installed().has("dsh-host-bridge")) {
      return `${tool} is provided by the DSH app's host bridge, which is not loaded: start DSH from the app`;
    }
    const shipped = shippedTools();
    if (!allowPlugins && shipped && !shipped.has(tool)) {
      // Tools the image itself registers stay allowed; anything a plugin
      // added beyond the app's manifest entry does not.
      return `${tool} is not part of this DSH image's tool set (plugin tools are switched off in DSH's settings)`;
    }
    if (!allowPtcShell && exec?.engine === "ptc" && LOOP_OR_UI_TOOLS.includes(tool)) {
      return `${tool} cannot run from a program on iOS; call the tool directly instead`;
    }
    return undefined;
  });
}
