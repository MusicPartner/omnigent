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

function sameHostDirectory(a: string, b: string): boolean {
  if (isWindowsDrivePath(a) && isWindowsDrivePath(b)) {
    return a.replace(/\\/g, "/").toLowerCase() === b.replace(/\\/g, "/").toLowerCase();
  }
  return a === b;
}

/**
 * True when the path is already an absolute host path: POSIX ``/…``
 * or a Windows drive path (``C:\\…`` / ``C:/…``).
 */
export function isHostAbsolutePath(path: string): boolean {
  return path.startsWith("/") || isWindowsDrivePath(path);
}

/**
 * Join a directory path and a new child name into an absolute path.
 *
 * Handles the filesystem root (``"/"`` + ``"foo"`` → ``"/foo"`` rather
 * than ``"//foo"``) and trims a trailing slash off the parent so a
 * typed ``"/Users/me/"`` still produces ``"/Users/me/foo"``. Windows
 * drive roots (``C:\\``) join with a backslash. The child name is
 * trimmed; surrounding/duplicate slashes in it are left to the host
 * to resolve.
 *
 * @param dir Absolute parent directory, e.g. ``"/Users/me"`` or ``"/"``.
 * @param name New child name, e.g. ``"new-app"``.
 * @returns The joined absolute path, e.g. ``"/Users/me/new-app"``.
 */
export function joinPath(dir: string, name: string): string {
  const trimmedName = name.trim();
  if (dir === "/") {
    return `/${trimmedName}`;
  }
  if (/^[A-Za-z]:[\\/]?$/.test(dir)) {
    const sep = dir.includes("\\") || dir.endsWith("\\") ? "\\" : "/";
    const root = dir.length === 2 ? `${dir}${sep}` : dir.endsWith(sep) ? dir : `${dir}${sep}`;
    return `${root}${trimmedName}`;
  }
  const sep = separatorOf(dir);
  const base =
    dir.endsWith("/") || (isWindowsDrivePath(dir) && dir.endsWith("\\")) ? dir.slice(0, -1) : dir;
  return `${base}${sep}${trimmedName}`;
}

/**
 * Compute the parent directory of an absolute path.
 *
 * Returns ``null`` when the input is empty (host's home view —
 * has no parent in the picker's UX) or already at the root
 * ``"/"`` / ``C:\\``. Otherwise drops the last segment.
 *
 * @param absolutePath Absolute path or empty string.
 * @returns Parent path, or ``null`` if there is no further parent.
 */
export function parentOf(absolutePath: string): string | null {
  if (absolutePath === "" || absolutePath === "/") {
    return null;
  }
  if (/^[A-Za-z]:[\\/]?$/.test(absolutePath)) {
    return null;
  }
  const stripped =
    absolutePath.endsWith("/") || (isWindowsDrivePath(absolutePath) && absolutePath.endsWith("\\"))
      ? absolutePath.slice(0, -1)
      : absolutePath;
  if (/^[A-Za-z]:$/.test(stripped)) {
    return null;
  }
  const idx = lastSeparatorIndex(stripped);
  if (idx < 0) {
    return null;
  }
  // ``C:\\Users`` → ``C:\\`` (keep the drive root, never POSIX ``/``).
  if (isWindowsDrivePath(stripped) && idx === 2) {
    return stripped.slice(0, 3);
  }
  if (idx === 0) {
    return "/";
  }
  return stripped.slice(0, idx);
}

/**
 * Normalize a path the user typed into the path input.
 *
 * Trims whitespace, expands a leading ``~`` against the resolved
 * home directory, collapses runs of slashes, and drops a trailing
 * slash (except on the root ``"/"`` / ``C:\\``). Returns ``null`` for
 * empty or invalid inputs (which the caller treats as "ignore —
 * keep the current path"). Windows drive-letter paths are accepted
 * as already-absolute.
 *
 * @param input Whatever the user typed, e.g.
 *   ``"  /Users//corey/  "`` or ``"~/projects"``.
 * @param home Resolved absolute path of the host's home dir, or
 *   ``null`` if not yet known.
 * @returns Cleaned absolute path (e.g. ``"/Users/corey"``) or
 *   ``null`` when the input isn't usable.
 */
export function normalizeTypedPath(input: string, home: string | null = null): string | null {
  const trimmed = input.trim();
  if (trimmed === "") {
    return null;
  }
  let absolute: string;
  if (trimmed === "~") {
    if (home === null) return null;
    absolute = home;
  } else if (trimmed.startsWith("~/") || (home !== null && trimmed.startsWith("~\\"))) {
    if (home === null) return null;
    absolute = joinPath(home, trimmed.slice(2));
  } else if (isHostAbsolutePath(trimmed)) {
    absolute = trimmed;
  } else {
    return null;
  }
  if (isWindowsDrivePath(absolute) || absolute.startsWith("\\\\")) {
    const sep = separatorOf(absolute);
    const collapsed = absolute.replace(/[\\/]+/g, sep);
    if (/^[A-Za-z]:[\\/]$/.test(collapsed)) {
      return collapsed;
    }
    return collapsed.endsWith(sep) ? collapsed.slice(0, -1) : collapsed;
  }
  const collapsed = absolute.replace(/\/+/g, "/");
  if (collapsed === "/") {
    return "/";
  }
  return collapsed.endsWith("/") ? collapsed.slice(0, -1) : collapsed;
}

/**
 * True when a path can be opened in the picker: an absolute path or a
 * home-relative one (``~`` / ``~/foo``). The host expands ``~`` server
 * side, so these navigate fine; relative paths and the ``~user`` form
 * do not and are rejected.
 *
 * @param path Raw path text, e.g. ``"~/projects"`` or ``"/tmp"``.
 * @returns Whether the picker can navigate to it.
 */
export function isNavigablePath(path: string): boolean {
  const trimmed = path.trim();
  return (
    isHostAbsolutePath(trimmed) ||
    trimmed === "~" ||
    trimmed.startsWith("~/") ||
    trimmed.startsWith("~\\")
  );
}

/**
 * Expand a typed workspace value to the absolute path the server needs,
 * resolving a leading ``~`` against the host's home. Returns the absolute
 * path, or ``null`` when it can't be resolved yet — a ``~``-path whose home
 * hasn't loaded, or an unusable (relative / empty) value.
 *
 * A POSIX-absolute value is preserved verbatim (only trailing slashes are
 * stripped, keeping root ``"/"``) — matching the prior ``normalizeWorkspacePath``
 * so an existing accepted path is never rewritten. Only a ``~``-relative (or
 * Windows drive) value goes through ``normalizeTypedPath``, which expands home
 * and collapses slash runs; routing an absolute path through it would rewrite
 * a typed leading ``"//foo"`` to ``"/foo"``.
 *
 * @param value Raw workspace text, e.g. ``"~/projects/app"`` or ``"/tmp"``.
 * @param home Resolved absolute home, or ``null`` if not yet known.
 * @returns The absolute workspace, or ``null`` when unresolved/unusable.
 */
export function resolveWorkspacePath(value: string, home: string | null): string | null {
  const trimmed = value.trim();
  if (trimmed.startsWith("/")) {
    const stripped = trimmed.replace(/\/+$/, "");
    return stripped === "" ? "/" : stripped;
  }
  return normalizeTypedPath(trimmed, home);
}

export function listingFilter(
  pathInput: string,
  currentAbsolute: string,
  home: string | null = null,
): string | null {
  const trimmed = pathInput.trim();
  if (trimmed === "") return null;
  const slash = lastSeparatorIndex(trimmed);
  if (slash === -1) {
    // Bare fragment, no directory part → filter the current dir by it.
    return trimmed;
  }
  const partial = trimmed.slice(slash + 1);
  if (partial === "") return null; // "<dir>/" — nothing typed past the slash.
  // A fragment only filters when its directory part IS the current directory;
  // otherwise the user is typing a path elsewhere (navigation, not a filter).
  const dirText =
    trimmed.slice(0, slash) || (isWindowsDrivePath(trimmed) ? trimmed.slice(0, 3) : "/");
  const normalizedDir = normalizeTypedPath(dirText, home);
  if (normalizedDir === null) return null;
  return sameHostDirectory(normalizedDir, currentAbsolute) ? partial : null;
}
