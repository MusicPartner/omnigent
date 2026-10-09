"use strict";

const { execFile } = require("child_process");
const cli = require("./omnigent_cli");

const REQUEST_TIMEOUT_MS = 45000;
const EXIT_TIMEOUT_MS = 3000;

function hasExited(child) {
  return child.exitCode !== null || child.signalCode != null;
}

/**
 * Ask the Windows lifecycle helper to stop this exact spawned process tree.
 * The native helper signals graceful listeners and verifies descendant exit.
 */
async function stopOwnedHost(child, command, createdBeforeMs) {
  if (!child || hasExited(child) || !Number.isInteger(child.pid)) return;
  let resolveExit;
  const exited = new Promise((resolve) => {
    resolveExit = resolve;
  });
  child.once("exit", resolveExit);
  try {
    try {
      const { executable, prefixArgs } = cli.cliCommandParts(command);
      await new Promise((resolve, reject) => {
        execFile(
          executable,
          [
            ...prefixArgs,
            "_internal",
            "windows-shutdown",
            String(child.pid),
            "--grace-seconds",
            "30",
            "--created-before-ms",
            String(createdBeforeMs),
          ],
          { timeout: REQUEST_TIMEOUT_MS, windowsHide: true, encoding: "utf8" },
          (error, _stdout, stderr) => {
            if (error) {
              reject(new Error(`Windows host shutdown failed: ${stderr?.trim() || error.message}`));
            } else {
              resolve();
            }
          },
        );
      });
    } catch (error) {
      console.error(error);
      throw error;
    }
    if (!hasExited(child)) {
      let timer;
      try {
        await Promise.race([
          exited,
          new Promise((_, reject) => {
            timer = setTimeout(
              () => reject(new Error(`Windows host ${child.pid} did not exit after shutdown`)),
              EXIT_TIMEOUT_MS,
            );
          }),
        ]);
      } finally {
        clearTimeout(timer);
      }
    }
  } finally {
    child.removeListener("exit", resolveExit);
  }
}

module.exports = { stopOwnedHost };
