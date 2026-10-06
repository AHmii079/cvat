# Definition of Done

Written before starting. Each line gets a number, a link or a file path as evidence when ticked.
A line ticked without evidence counts as not done.

## Floor (items 1–4)

- [ ] Endpoint returns per-label counts that match the COCO JSON for the same images (script output in `docs/evidence/`).
- [ ] Page opens from the task page and draws a bar chart from the endpoint (screenshot).
- [ ] Task with no annotations shows an empty-state message, not an empty chart (screenshot).
- [ ] Failed request shows an error message with a retry action (screenshot, server stopped or 500 forced).

## Access (item 5)

- [ ] No login → 401 (curl output).
- [ ] Logged-in user with no access to the task → 403 (curl output).
- [ ] Task owner → 200 (curl output).

## Objective and filter (items 6–7)

- [ ] MO-1 measured: 1 warm-up + 5 runs, raw output saved, median and spread reported.
- [ ] MO-1 target met, or missed with the reason written down.
- [ ] `group_by=shape_type` returns counts per label and shape type, and the totals equal the plain counts.

## Hygiene

- [ ] The first commit holds only these docs; commits after it are small and say what changed and why.
- [ ] No dead code, no commented-out blocks, no stray files in the diff.
- [ ] Everything not finished is listed below with the reason.

## Not finished

(Filled in at the end.)
