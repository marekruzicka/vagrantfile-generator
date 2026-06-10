export function uniqueProjectName(label: string): string {
  return `E2E ${label} ${Date.now()} ${Math.random().toString(36).slice(2, 8)}`
}

export const projectDescription =
  'Created by Playwright E2E proof-of-concept tests for Projects Dashboard coverage.'
