/** True for Windows drive-letter paths such as `C:/Users/me` or `C:\\Users\\me`. */
export function isWindowsDrivePath(path: string): boolean {
  return /^[A-Za-z]:[\\/]/.test(path);
}

export function lastSeparatorIndex(path: string): number {
  if (isWindowsDrivePath(path)) {
    return Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
  }
  return path.lastIndexOf("/");
}

export function separatorOf(path: string): "/" | "\\" {
  return path.includes("\\") && !path.slice(path.indexOf(":") + 1).includes("/") ? "\\" : "/";
}

/**
 * Basename of an absolute path, for the "Select current" label.
 *
 * @param absolutePath Current directory, e.g.
 *   ``"/Users/corey/projects"``, ``"/"``, or ``""`` (home,
 *   pre-resolution).
 * @returns The last path segment (``"projects"``), ``"/"`` for the
 *   root, or ``"~"`` when the path is still the empty placeholder.
 */
export function basename(absolutePath: string): string {
  if (absolutePath === "") {
    return "~";
  }
  if (absolutePath === "/") {
    return "/";
  }
  if (/^[A-Za-z]:[\\/]?$/.test(absolutePath)) {
    return absolutePath.length >= 3 ? absolutePath.slice(0, 3) : `${absolutePath}\\`;
  }
  const stripped =
    absolutePath.endsWith("/") || (isWindowsDrivePath(absolutePath) && absolutePath.endsWith("\\"))
      ? absolutePath.slice(0, -1)
      : absolutePath;
  const sepIdx = lastSeparatorIndex(stripped);
  if (sepIdx < 0) {
    return stripped;
  }
  return stripped.slice(sepIdx + 1);
}
