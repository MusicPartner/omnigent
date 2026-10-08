import { basename, isWindowsDrivePath, separatorOf } from "./hostPaths";

export interface WorkspaceBreadcrumbItem {
  label: string;
  path: string;
}

/** Separator shown between breadcrumb segments for the current host path. */
export function workspaceBreadcrumbSeparator(path: string): "/" | "\\" {
  return isWindowsDrivePath(path) ? separatorOf(path) : "/";
}

/** Build clickable breadcrumbs without changing the host's path syntax. */
export function workspaceBreadcrumbItems(
  currentAbsolute: string,
  resolvedHome: string | null,
): WorkspaceBreadcrumbItem[] {
  if (currentAbsolute === "") {
    return [{ label: "~", path: "" }];
  }
  if (currentAbsolute === "/") {
    return [{ label: "/", path: "/" }];
  }

  if (resolvedHome !== null) {
    const normalizedCurrent = currentAbsolute.replace(/\\/g, "/");
    const normalizedHome = resolvedHome.replace(/\\/g, "/").replace(/\/$/, "");
    const windowsPaths = isWindowsDrivePath(currentAbsolute) && isWindowsDrivePath(resolvedHome);
    const comparableCurrent = windowsPaths ? normalizedCurrent.toLowerCase() : normalizedCurrent;
    const comparableHome = windowsPaths ? normalizedHome.toLowerCase() : normalizedHome;
    if (
      comparableCurrent === comparableHome ||
      comparableCurrent.startsWith(`${comparableHome}/`)
    ) {
      const relativeParts = normalizedCurrent
        .slice(normalizedHome.length)
        .split("/")
        .filter(Boolean);
      const sep = separatorOf(resolvedHome);
      const home = resolvedHome.replace(/[\\/]$/, "");
      return [
        { label: basename(resolvedHome), path: resolvedHome },
        ...relativeParts.map((label, index) => ({
          label,
          path: `${home}${sep}${relativeParts.slice(0, index + 1).join(sep)}`,
        })),
      ];
    }
  }

  if (isWindowsDrivePath(currentAbsolute)) {
    const sep = separatorOf(currentAbsolute);
    const root = `${currentAbsolute.slice(0, 2)}${sep}`;
    const parts = currentAbsolute.slice(3).split(/[\\/]/).filter(Boolean);
    return [
      { label: currentAbsolute.slice(0, 2), path: root },
      ...parts.map((label, index) => ({
        label,
        path: `${root}${parts.slice(0, index + 1).join(sep)}`,
      })),
    ];
  }

  const parts = currentAbsolute.split("/").filter(Boolean);
  return [
    { label: "/", path: "/" },
    ...parts.map((label, index) => ({
      label,
      path: `/${parts.slice(0, index + 1).join("/")}`,
    })),
  ];
}
