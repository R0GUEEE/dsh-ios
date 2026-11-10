/**
 * dsh-ios-mcp — mounts the user's MCP servers from one editable file.
 *
 * A patch layer cannot express a variable number of servers: each server is
 * its own `mcp-client` row with its own `serverName`, and the user adds and
 * removes them at runtime. So this plugin reads `~/.dsh/mcp.json`, validates
 * every entry, and asks the loader for one `@deepseek-ai/dsh-mcp-client` per
 * server — the same plugin the shipped bundle mounts, with the same config
 * union (`stdio` | `streamable-http`).
 *
 * File shape (all keys except name/transport/command or url are optional):
 *
 *   {
 *     "servers": {
 *       "github": {
 *         "transport": "stdio",
 *         "command": "npx",
 *         "args": ["-y", "@modelcontextprotocol/server-github"],
 *         "env": { "GITHUB_TOKEN": "$GITHUB_TOKEN" }
 *       },
 *       "docs": { "transport": "streamable-http", "url": "https://example.com/mcp" }
 *     }
 *   }
 *
 * Rules this enforces, because a bad entry fails at boot and takes the whole
 * harness with it:
 *
 * - `serverName` is the map key; it must match the client's own pattern
 *   `[A-Za-z0-9_-]{1,32}`, since a second registration under one name throws.
 * - `env` values may be `$NAME`, resolved from the guest environment at
 *   launch. The file is user-editable and sits in the harness home, which is
 *   outside the app's build, so a token pasted there is not baked into the
 *   image — but it is also not secure storage, and the agent runs as root.
 * - A malformed entry is skipped with a log line naming it, rather than
 *   refusing the file: one typo must not disable every other server.
 *
 * Reloading: the file is watched by Cordis HMR only if it is part of a module
 * root; here the plugin re-reads on `ctx.effect` disposal and on the
 * `mcp/reload` command, so `dsh-ios-mcp` reloads without a harness restart.
 *
 * @module dsh-ios-mcp
 */
import { readFileSync } from "node:fs";

export const name = "ios-mcp";

const CONFIG_FILE = process.env.DSH_MCP_CONFIG ?? "/root/.dsh/mcp.json";
const CLIENT = "@deepseek-ai/dsh-mcp-client";
const NAME_PATTERN = /^[A-Za-z0-9_-]{1,32}$/;

/** Substitute `$NAME` from the environment; leave anything else untouched. */
function expandEnv(value) {
  return String(value).replace(/\$([A-Za-z_][A-Za-z0-9_]*)/g, (whole, key) => process.env[key] ?? whole);
}

function expandMap(map) {
  if (!map || typeof map !== "object") return {};
  const out = {};
  for (const [key, value] of Object.entries(map)) out[key] = expandEnv(value);
  return out;
}

/**
 * Validate one server entry and return the config a client accepts, or an
 * explanation of why it cannot be mounted.
 */
function normalise(key, entry) {
  if (!NAME_PATTERN.test(key)) {
    return { problem: `server name "${key}" is invalid (letters, digits, _ and -, at most 32 characters)` };
  }
  if (!entry || typeof entry !== "object") return { problem: `${key}: entry must be an object` };

  const transport = entry.transport ?? "stdio";
  const base = {
    serverName: key,
    toolCallTimeoutMs: Number.isFinite(entry.toolCallTimeoutMs) ? entry.toolCallTimeoutMs : 60000,
    failOnStartupError: entry.failOnStartupError === true,
  };

  if (transport === "stdio") {
    if (typeof entry.command !== "string" || !entry.command.trim()) {
      return { problem: `${key}: stdio server needs a "command"` };
    }
    return {
      config: {
        ...base,
        transport: "stdio",
        command: entry.command,
        args: Array.isArray(entry.args) ? entry.args.map(String) : [],
        env: expandMap(entry.env),
        cwd: typeof entry.cwd === "string" ? entry.cwd : "",
      },
    };
  }
  if (transport === "streamable-http") {
    if (typeof entry.url !== "string" || !entry.url.trim()) {
      return { problem: `${key}: streamable-http server needs a "url"` };
    }
    try {
      new URL(entry.url);
    } catch {
      return { problem: `${key}: url is not absolute` };
    }
    return {
      config: { ...base, transport: "streamable-http", url: entry.url, headers: expandMap(entry.headers) },
    };
  }
  return { problem: `${key}: unknown transport "${transport}" (stdio or streamable-http)` };
}

function readServers(ctx) {
  let raw;
  try {
    raw = readFileSync(CONFIG_FILE, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return []; // no file: no servers, and no noise
    ctx.logger?.warn?.(`ios-mcp: cannot read ${CONFIG_FILE}: ${error.message}`);
    return [];
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    ctx.logger?.error?.(`ios-mcp: ${CONFIG_FILE} is not valid JSON (${error.message}); no MCP servers mounted`);
    return [];
  }
  const servers = parsed?.servers;
  if (!servers || typeof servers !== "object" || Array.isArray(servers)) {
    ctx.logger?.warn?.(`ios-mcp: ${CONFIG_FILE} has no "servers" object; no MCP servers mounted`);
    return [];
  }
  const out = [];
  for (const [key, entry] of Object.entries(servers)) {
    const result = normalise(key, entry);
    if (result.problem) {
      ctx.logger?.warn?.(`ios-mcp: skipped: ${result.problem}`);
      continue;
    }
    out.push(result.config);
  }
  return out;
}

export async function apply(ctx) {
  const mounted = new Map();

  const mount = async () => {
    for (const config of readServers(ctx)) {
      if (mounted.has(config.serverName)) continue;
      try {
        // One row per server, exactly as the shipped bundle does it: the
        // loader owns lifetimes, so a harness restart tears every child down.
        const fiber = await ctx.loader.create({ name: CLIENT, config });
        mounted.set(config.serverName, fiber);
        ctx.logger?.info?.(`ios-mcp: mounted "${config.serverName}" (${config.transport})`);
      } catch (error) {
        // A failing server is named and skipped: `failOnStartupError: false`
        // is the client's default for the same reason.
        ctx.logger?.warn?.(`ios-mcp: "${config.serverName}" failed to mount: ${error?.message ?? error}`);
      }
    }
  };

  await mount();

  // `dsh ios-mcp reload` (or the Settings menu) re-reads the file.
  ctx.on("mcp/reload", () => { void mount(); });
}
