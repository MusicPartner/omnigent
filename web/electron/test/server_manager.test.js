// Tests for desktop-owned Windows host cleanup and the auth gate in
// src/server_manager.js, run with `node --test`. Spawned processes are fakes;
// authentication covers loopback skip → /v1/me probe → login → error.
//
// `server_manager` captures the `omnigent_cli` module object once at require
// time, so mocking methods on that same shared object (via `mock.method`) is
// seen by the code under test.

const { describe, it, mock, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const cli = require("../src/omnigent_cli");
const { ensureServerAuth } = require("../src/server_manager");

const SERVER = "https://app.example.com";
const CLI_PATH = "/bin/omnigent";

function windowsManager({
  connected = false,
  autoConnect = true,
  failSpawn = false,
  serverStops = [],
} = {}) {
  const children = [];
  const requests = [];
  const spawnOptions = [];
  const serverStopCalls = [];
  const errors = [];
  const command = { executable: "uv.exe", prefixArgs: ["run", "omnigent"] };
  const managerCli = {
    cliCommandParts: cli.cliCommandParts,
    normalizeServerUrl: (value) => value.replace(/\/+$/, ""),
    getHostConnectionFast: async () => ({ connected }),
    localServerHealthy: async () => null,
    startLocalServer: async () => ({
      ok: true,
      url: "http://localhost:6767",
      port: 6767,
      pid: 9876,
    }),
    stopLocalServer: async (ownCommand) => {
      serverStopCalls.push(ownCommand);
      return serverStops.shift() || { ok: true };
    },
    stopHost: async () => {
      throw new Error("An owned host must not use target-based stop");
    },
  };
  const module = { exports: {} };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../src/server_manager.js"), "utf8"), {
    module,
    console: { error: (error) => errors.push(error) },
    process: { platform: "win32" },
    setTimeout,
    clearTimeout,
    require(name) {
      if (name === "./omnigent_cli") return managerCli;
      if (name === "./windows_host_shutdown") {
        return {
          stopOwnedHost(child, ownCommand, createdBeforeMs) {
            if (!child || child.exitCode !== null || !child.pid) return Promise.resolve();
            let finish;
            const promise = new Promise((resolve) => {
              finish = () => {
                child.exitCode = 0;
                child.emit("exit", 0, null);
                resolve();
              };
            });
            requests.push({ child, command: ownCommand, createdBeforeMs, finish });
            return promise;
          },
        };
      }
      if (name === "child_process") {
        return {
          spawn(_executable, _args, options) {
            const child = Object.assign(new EventEmitter(), {
              pid: failSpawn ? undefined : 1234 + children.length,
              exitCode: null,
              killed: false,
              stdout: new EventEmitter(),
              stderr: new EventEmitter(),
              kill() {
                throw new Error("Windows shutdown must use the native helper");
              },
            });
            children.push(child);
            spawnOptions.push(options);
            queueMicrotask(() => {
              if (failSpawn) child.emit("error", new Error("ENOENT"));
              else if (autoConnect) child.stdout.emit("data", Buffer.from("✓ Connected"));
            });
            return child;
          },
        };
      }
      throw new Error(`Unexpected require: ${name}`);
    },
  });
  return {
    manager: module.exports,
    children,
    requests,
    spawnOptions,
    command,
    serverStopCalls,
    errors,
  };
}

describe("Windows desktop-owned host shutdown", () => {
  it("uses the exact spawned command and waits for native cleanup before returning", async () => {
    const fixture = windowsManager();
    await fixture.manager.ensureHostConnected(fixture.command, SERVER);
    assert.equal(fixture.spawnOptions[0].windowsHide, true);
    let completed = false;
    const shutdown = fixture.manager.shutdown(null).then(() => {
      completed = true;
    });
    assert.equal(fixture.requests.length, 1);
    assert.equal(fixture.requests[0].command, fixture.command);
    assert.ok(Number.isInteger(fixture.requests[0].createdBeforeMs));
    assert.equal(fixture.requests[0].child, fixture.children[0]);
    await Promise.resolve();
    assert.equal(completed, false);
    fixture.requests[0].finish();
    await shutdown;
    assert.equal(fixture.manager.ownsLiveHost(SERVER), false);
  });

  it("covers a spawned host before its connected marker and deduplicates overlapping cleanup", async () => {
    const fixture = windowsManager({ autoConnect: false });
    const connecting = fixture.manager.ensureHostConnected(fixture.command, SERVER);
    await new Promise(setImmediate);
    const shutdown = fixture.manager.shutdown(null);
    const secondShutdown = fixture.manager.shutdown(null);
    assert.equal(fixture.requests.length, 1);
    fixture.requests[0].finish();
    await Promise.all([shutdown, secondShutdown]);
    const result = await connecting;
    assert.equal(result.ok, false);
    assert.equal(fixture.requests.length, 1);
  });

  it("leaves a reused host alone at quit", async () => {
    const fixture = windowsManager({ connected: true });
    const result = await fixture.manager.ensureHostConnected(fixture.command, SERVER);
    assert.equal(result.ownedByDesktop, false);
    await fixture.manager.shutdown(null);
    assert.equal(fixture.children.length, 0);
    assert.equal(fixture.requests.length, 0);
  });

  it("settles spawn errors without requesting shutdown of an unknown PID", async () => {
    const fixture = windowsManager({ failSpawn: true });
    const result = await fixture.manager.ensureHostConnected(fixture.command, SERVER);
    assert.equal(result.ok, false);
    await fixture.manager.shutdown(null);
    assert.equal(fixture.requests.length, 0);
  });

  it("reports a failed server stop and retains ownership until a successful retry", async () => {
    const fixture = windowsManager({ serverStops: [{ ok: false }, { ok: true }] });
    await fixture.manager.startLocalServer(fixture.command);
    await assert.rejects(fixture.manager.shutdown(fixture.command), (error) => {
      assert.equal(error.message, "Desktop shutdown failed");
      assert.equal(error.errors[0].message, "Local server shutdown failed");
      return true;
    });
    assert.equal(fixture.errors.length, 1);
    assert.equal(fixture.serverStopCalls.length, 1);
    const retry = await fixture.manager.stopOwnedLocalServer(fixture.command);
    assert.equal(retry.ok, true);
    assert.equal(fixture.serverStopCalls.length, 2);
    assert.equal(fixture.serverStopCalls[1], fixture.command);
    const skipped = await fixture.manager.stopOwnedLocalServer(fixture.command);
    assert.equal(skipped.skipped, true);
    assert.equal(fixture.serverStopCalls.length, 2);
  });
});

describe("ensureServerAuth", () => {
  afterEach(() => {
    mock.restoreAll();
  });

  it("skips auth entirely for a loopback server (no probe, no login)", async () => {
    mock.method(cli, "isLoopbackServer", () => true);
    const probe = mock.method(cli, "probeServerAuth", async () => ({
      authed: false,
      reachable: true,
    }));
    const login = mock.method(cli, "loginServer", async () => ({ ok: false, output: "" }));

    const res = await ensureServerAuth(CLI_PATH, "http://localhost:6767");

    assert.deepEqual(res, { ok: true });
    assert.equal(probe.mock.callCount(), 0);
    assert.equal(login.mock.callCount(), 0);
  });

  it("skips login when the probe reports already authed", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: true, reachable: true }));
    const login = mock.method(cli, "loginServer", async () => ({ ok: false, output: "" }));
    const onLogin = mock.fn();

    const res = await ensureServerAuth(CLI_PATH, SERVER, { onLogin });

    assert.deepEqual(res, { ok: true });
    assert.equal(login.mock.callCount(), 0);
    assert.equal(onLogin.mock.callCount(), 0);
  });

  it("skips login (defers to the connect attempt) when the server is unreachable", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: false, reachable: false }));
    const login = mock.method(cli, "loginServer", async () => ({ ok: false, output: "" }));

    const res = await ensureServerAuth(CLI_PATH, SERVER);

    assert.deepEqual(res, { ok: true });
    assert.equal(login.mock.callCount(), 0);
  });

  it("runs login when not authed, and returns ok on success", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: false, reachable: true }));
    const login = mock.method(cli, "loginServer", async () => ({ ok: true, output: "Logged in." }));
    const onLogin = mock.fn();

    const res = await ensureServerAuth(CLI_PATH, SERVER, { onLogin });

    assert.deepEqual(res, { ok: true });
    assert.equal(login.mock.callCount(), 1);
    assert.equal(onLogin.mock.callCount(), 1);
    assert.deepEqual(login.mock.calls[0].arguments, [CLI_PATH, SERVER]);
  });

  it("passes an isaac omni descriptor through login and names it in the safe error", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: false, reachable: true }));
    const login = mock.method(cli, "loginServer", async () => ({ ok: false, output: "SECRET" }));
    const command = {
      executable: "/usr/local/bin/isaac",
      prefixArgs: ["omni"],
      displayName: "isaac omni",
    };

    const res = await ensureServerAuth(command, SERVER);

    assert.deepEqual(login.mock.calls[0].arguments, [command, SERVER]);
    assert.equal(res.authError, true);
    assert.match(res.error, /isaac omni login https:\/\/app\.example\.com/);
    assert.doesNotMatch(res.error, /SECRET/);
  });

  it("returns an authError with a generic message and does NOT surface raw login output", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: false, reachable: true }));
    // `omnigent login` stdout on the OIDC path can carry the login-ticket URL
    // (auth material); it must never reach the renderer via the error string.
    mock.method(cli, "loginServer", async () => ({
      ok: false,
      output: "Opening browser for login: https://app.example.com/auth/login?ticket=SECRET123",
    }));

    const res = await ensureServerAuth(CLI_PATH, SERVER);

    assert.equal(res.ok, false);
    assert.equal(res.authError, true);
    assert.doesNotMatch(res.error, /ticket=|SECRET123/);
    assert.match(res.error, /omnigent login https:\/\/app\.example\.com/);
  });

  it("uses the same generic message when login fails with no output", async () => {
    mock.method(cli, "isLoopbackServer", () => false);
    mock.method(cli, "probeServerAuth", async () => ({ authed: false, reachable: true }));
    mock.method(cli, "loginServer", async () => ({ ok: false, output: "" }));

    const res = await ensureServerAuth(CLI_PATH, SERVER);

    assert.equal(res.ok, false);
    assert.equal(res.authError, true);
    assert.match(res.error, /omnigent login https:\/\/app\.example\.com/);
  });
});
