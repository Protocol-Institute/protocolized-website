// Work-in-progress projects: front-end working documents (e.g. a proceedings
// volume gathering drafts) that will eventually become items in the resource
// archive. Each project's source of truth is wip/<slug>/project.json at the
// repo root, bundled into the Worker at build time, so a page update is a
// commit + push. scripts/wip/build-manuscript.py writes the "versions" list
// when it publishes a new manuscript to R2.

import protocolReaderVol2 from "../../wip/protocol-reader-vol-2/project.json";
import protocolReaderVol2Checks from "../../wip/protocol-reader-vol-2/checks.json";

export interface WipReadiness {
  score: number;
  note: string;
  assessed: string;
  assessed_hash?: string;
  stale?: boolean;
}

export interface WipEntry {
  id: string;
  part: string;
  title: string;
  authors: string[];
  summary: string;
  talk?: string;
  source: { kind: string; id?: string; name?: string; path?: string };
  readiness: WipReadiness;
  checklist?: boolean;
}

// One changelog entry per published manuscript. `message` is also the git
// commit message of the release (build-manuscript.py writes both). Only the
// latest version keeps a `file`: older PDFs are archived locally, not served.
export interface WipVersion {
  version: string;
  date: string;
  file: string | null;
  pages: number;
  added: string[];
  updated: string[];
  message: string;
}

export interface WipChecklistItem {
  id: string;
  section: string;
  label: string;
  detail: string;
  auto: boolean;
  advisory?: boolean;
  licenses?: string[];
}

export type CheckStatus = "pass" | "fail" | "warn" | "manual" | "na";

// Written by scripts/wip/check-drafts.py (and on each published build).
export interface WipChecks {
  generated: string;
  entries: Record<string, {
    results: Record<string, { status: CheckStatus; detail: string }>;
    summary: { pass: number; fail: number; warn: number; manual: number; na: number; ready: boolean };
  }>;
}

export interface WipProject {
  slug: string;
  title: string;
  subtitle?: string;
  editor?: string;
  kind: string;
  stage: string;
  started: string;
  description: string;
  cover?: string;
  readiness_scale: Record<string, string>;
  deadline?: { date: string; label: string; detail: string };
  checklist?: WipChecklistItem[];
  checks?: WipChecks;
  parts: { id: string; title: string }[];
  contents: WipEntry[];
  versions: WipVersion[];
}

// Register new projects here.
const PROJECTS: WipProject[] = [
  { ...(protocolReaderVol2 as unknown as WipProject), checks: protocolReaderVol2Checks as WipChecks },
];

export function getWipProjects(): WipProject[] {
  return PROJECTS;
}

export function getWipProject(slug: string): WipProject | undefined {
  return PROJECTS.find((p) => p.slug === slug);
}

export const WIP_STAGES: Record<string, string> = {
  gathering: "Gathering drafts",
  editing: "In editing",
  production: "In production",
  published: "Published",
};
