import { describe, expect, it } from "vitest";

import {
  isHostAbsolutePath,
  isNavigablePath,
  joinPath,
  listingFilter,
  normalizeTypedPath,
  parentOf,
  resolveWorkspacePath,
} from "./hostPaths";

describe("host path helpers", () => {
  it("preserves drive roots, separator style, and Windows case-insensitive matching", () => {
    expect(parentOf("C:\\")).toBeNull();
    expect(parentOf("C:\\Users\\me")).toBe("C:\\Users");
    expect(joinPath("C:\\", " child ")).toBe("C:\\child");
    expect(listingFilter("c:\\users\\alice\\pro", "C:\\Users\\Alice")).toBe("pro");
  });

  it("keeps POSIX backslashes as characters and comparisons case-sensitive", () => {
    expect(parentOf("/tmp/a\\b")).toBe("/tmp");
    expect(listingFilter("/TMP/pro", "/tmp")).toBeNull();
  });

  it("expands home paths without rewriting absolute resolver slash runs", () => {
    expect(normalizeTypedPath("~/src", "/Users/me")).toBe("/Users/me/src");
    expect(resolveWorkspacePath("//foo", null)).toBe("//foo");
    expect(resolveWorkspacePath("/a//b", null)).toBe("/a//b");
  });

  it("distinguishes navigable paths from unresolved relative values", () => {
    expect(isHostAbsolutePath("C:/Users/me")).toBe(true);
    expect(isNavigablePath("~/project")).toBe(true);
    expect(isNavigablePath("relative/project")).toBe(false);
  });
});
