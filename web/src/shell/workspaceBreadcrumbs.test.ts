import { describe, expect, it } from "vitest";

import { workspaceBreadcrumbItems, workspaceBreadcrumbSeparator } from "./workspaceBreadcrumbs";

describe("workspaceBreadcrumbItems", () => {
  it("keeps a backslash Windows drive path native and segment-addressable", () => {
    expect(workspaceBreadcrumbItems("C:\\Temp\\Share", null)).toEqual([
      { label: "C:", path: "C:\\" },
      { label: "Temp", path: "C:\\Temp" },
      { label: "Share", path: "C:\\Temp\\Share" },
    ]);
    expect(
      workspaceBreadcrumbItems("C:\\Temp\\Share", null)
        .map(({ label }) => label)
        .join(workspaceBreadcrumbSeparator("C:\\Temp\\Share")),
    ).toBe("C:\\Temp\\Share");
  });

  it("keeps forward-slash Windows drive paths in their original syntax", () => {
    expect(workspaceBreadcrumbItems("C:/Temp/Share", null)).toEqual([
      { label: "C:", path: "C:/" },
      { label: "Temp", path: "C:/Temp" },
      { label: "Share", path: "C:/Temp/Share" },
    ]);
    expect(workspaceBreadcrumbSeparator("C:/Temp/Share")).toBe("/");
  });

  it("recognizes Windows home descendants case-insensitively", () => {
    expect(workspaceBreadcrumbItems("C:\\Users\\Alice\\repo", "c:\\users\\alice")).toEqual([
      { label: "alice", path: "c:\\users\\alice" },
      { label: "repo", path: "c:\\users\\alice\\repo" },
    ]);
  });
});
