const { it } = require("node:test");
const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createRequire } = require("node:module");
const cli = require("../src/omnigent_cli");

function helperFixture(execute, { shortTimeout = false } = {}) {
  const calls = [];
  const errors = [];
  const child = Object.assign(new EventEmitter(), {
    pid: 789,
    exitCode: null,
    signalCode: null,
    kill(signal) {
      calls.push(signal);
      if (!shortTimeout) {
        child.signalCode = signal;
        child.emit("exit", null, signal);
      }
    },
  });
  const module = { exports: {} };
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "../src/windows_host_shutdown.js"), "utf8"),
    {
      module,
      console: { error: (error) => errors.push(error.message) },
      setTimeout: shortTimeout ? (fn) => setTimeout(fn, 1) : setTimeout,
      clearTimeout,
      require(name) {
        if (name === "./omnigent_cli") return cli;
        if (name === "child_process") {
          return { execFile: (...args) => execute(child, calls, ...args) };
        }
        throw new Error(`Unexpected require: ${name}`);
      },
    },
  );
  return { child, calls, errors, stop: module.exports.stopOwnedHost };
}

it("invokes native shutdown without a shell using the original CLI descriptor", async () => {
  const fixture = helperFixture((child, calls, executable, args, options, callback) => {
    calls.push({ executable, args, options });
    child.exitCode = 0;
    child.emit("exit", 0, null);
    callback(null, "", "");
  });
  await fixture.stop(
    fixture.child,
    {
      executable: "uv.exe",
      prefixArgs: ["run", "omnigent"],
    },
    123456,
  );
  const call = fixture.calls[0];
  assert.equal(call.executable, "uv.exe");
  assert.deepEqual(Array.from(call.args), [
    "run",
    "omnigent",
    "_internal",
    "windows-shutdown",
    "789",
    "--grace-seconds",
    "30",
    "--created-before-ms",
    "123456",
  ]);
  assert.equal(call.options.windowsHide, true);
  assert.equal(call.options.timeout, 45000);
  assert.equal(call.options.shell, undefined);
  assert.equal(fixture.child.listenerCount("exit"), 0);
});

it("waits for the original child exit after the native requester completes", async () => {
  const fixture = helperFixture((_child, _calls, _executable, _args, _options, callback) => {
    callback(null, "", "");
  });
  let completed = false;
  const stopping = fixture.stop(fixture.child, "omnigent.exe").then(() => {
    completed = true;
  });
  await Promise.resolve();
  assert.equal(completed, false);
  fixture.child.exitCode = 0;
  fixture.child.emit("exit", 0, null);
  await stopping;
});

it("allows native descendant cleanup to finish after the original child exits", async () => {
  let finishRequest;
  const fixture = helperFixture((_child, _calls, _executable, _args, _options, callback) => {
    finishRequest = callback;
  });
  let completed = false;
  const stopping = fixture.stop(fixture.child, "omnigent.exe", 123456).then(() => {
    completed = true;
  });
  fixture.child.exitCode = 0;
  fixture.child.emit("exit", 0, null);
  await Promise.resolve();
  assert.equal(completed, false);
  finishRequest(null, "", "");
  await stopping;
  assert.equal(fixture.child.listenerCount("exit"), 0);
});

it("reports an old CLI helper failure without force-killing only the root", async () => {
  const fixture = helperFixture((_child, _calls, _executable, _args, _options, callback) => {
    callback(new Error("command failed"), "", "unknown command");
  });
  await assert.rejects(fixture.stop(fixture.child, "omnigent.exe"), /unknown command/);
  assert.deepEqual(fixture.calls, []);
  assert.match(fixture.errors[0], /unknown command/);
});

it("reports a missing CLI helper without force-killing only the root", async () => {
  const fixture = helperFixture((_child, _calls, _executable, _args, _options, callback) => {
    callback(Object.assign(new Error("ENOENT"), { code: "ENOENT" }), "", "");
  });
  await assert.rejects(fixture.stop(fixture.child, "omnigent.exe"), /ENOENT/);
  assert.deepEqual(fixture.calls, []);
  assert.equal(fixture.child.listenerCount("exit"), 0);
});

it("bounds the wait if a successful native request produces no original child exit", async () => {
  const fixture = helperFixture(
    (_child, _calls, _executable, _args, _options, callback) => {
      callback(null, "", "");
    },
    { shortTimeout: true },
  );
  await assert.rejects(fixture.stop(fixture.child, "omnigent.exe"), /did not exit/);
  assert.deepEqual(fixture.calls, []);
  assert.equal(fixture.child.listenerCount("exit"), 0);
});

it("does not request shutdown for an already exited or never spawned child", async () => {
  const fixture = helperFixture(() => {
    throw new Error("Unexpected requester");
  });
  fixture.child.signalCode = "SIGTERM";
  await fixture.stop(fixture.child, "omnigent.exe");
  fixture.child.signalCode = null;
  fixture.child.pid = undefined;
  await fixture.stop(fixture.child, "omnigent.exe");
  assert.equal(fixture.calls.length, 0);
});

it("does not force-kill when the native requester rejects a process identity", async () => {
  const fixture = helperFixture((_child, _calls, _executable, _args, _options, callback) => {
    callback(
      Object.assign(new Error("exit 1"), { code: 1 }),
      "",
      "process birth is newer than spawn",
    );
  });
  await assert.rejects(
    fixture.stop(fixture.child, "omnigent.exe", 123456),
    /process birth is newer/,
  );
  assert.equal(fixture.calls.length, 0);
  assert.equal(fixture.child.listenerCount("exit"), 0);
});

it("does not force-kill an original child that exited while the requester was starting", async () => {
  const fixture = helperFixture((child, _calls, _executable, _args, _options, callback) => {
    child.exitCode = 0;
    child.emit("exit", 0, null);
    callback(Object.assign(new Error("ENOENT"), { code: "ENOENT" }), "", "");
  });
  await assert.rejects(fixture.stop(fixture.child, "omnigent.exe", 123456), /ENOENT/);
  assert.equal(fixture.calls.length, 0);
});

for (const [platform, expectedTimeout] of [
  ["win32", 45000],
  ["linux", 15000],
]) {
  it(`allows the host stop grace period on ${platform}`, async () => {
    const sourcePath = path.join(__dirname, "../src/omnigent_cli.js");
    const sourceRequire = createRequire(sourcePath);
    const calls = [];
    const module = { exports: {} };
    vm.runInNewContext(fs.readFileSync(sourcePath, "utf8"), {
      module,
      process: { ...process, platform },
      require(name) {
        if (name === "child_process") {
          return {
            execFile(executable, args, options, callback) {
              calls.push({ executable, args, options });
              callback(null, "Stopped", "");
            },
          };
        }
        return sourceRequire(name);
      },
    });
    const result = await module.exports.stopHost(
      { executable: "uv.exe", prefixArgs: ["run", "omnigent"] },
      "https://app.example.com",
    );
    assert.equal(result.ok, true);
    assert.equal(calls[0].executable, "uv.exe");
    assert.deepEqual(Array.from(calls[0].args), [
      "run",
      "omnigent",
      "host",
      "stop",
      "--server",
      "https://app.example.com",
    ]);
    assert.equal(calls[0].options.timeout, expectedTimeout);
  });
}
