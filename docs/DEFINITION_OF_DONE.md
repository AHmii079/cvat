# Definition of Done

Written before starting. Each line gets a number, a link or a file path as evidence when ticked.
A line ticked without evidence counts as not done.

## Floor (items 1–4)

- [x] Endpoint returns per-label counts that match the COCO JSON for the same images (script output in `docs/evidence/`).
  Evidence: `docs/evidence/counts.txt`, 80 of 80 labels match, 3,953 shapes. The expected value is shapes, not COCO instances (see Plan, "Changes during the work").
- [x] Page opens from the task page and draws a bar chart from the endpoint (screenshot). Evidence: `screenshots/chart.png`, task 1, 3,953 annotations across 80 labels. Reached from the task's Actions → Annotations per label.
- [x] Task with no annotations shows an empty-state message, not an empty chart (screenshot). Evidence: `screenshots/empty-state.png`, task 2 (one image, no annotations).
- [x] Failed request shows an error message with a retry action (screenshot, server stopped or 500 forced). Evidence: `screenshots/error-404.png` (task 999) and `screenshots/error-403.png` (tester on task 1). I showed 404 and 403 rather than a stopped server; both go through the same error branch, and an unreachable server falls back to the error's own message.

## Access (item 5)

- [x] No login → 401 (curl output). Evidence: `docs/evidence/access.txt`.
- [x] Logged-in user with no access to the task → 403 (curl output). Evidence: `docs/evidence/access.txt`, and `screenshots/tester-sees-no-tasks.png` shows the same user cannot see the task in CVAT's own list.
- [x] Task owner → 200 (curl output). Evidence: `docs/evidence/access.txt`.

## Objective and filter (items 6–7)

- [x] MO-1 measured: 1 warm-up + 5 runs, raw output saved, median and spread reported. Evidence: `docs/evidence/mo1.txt`, median 42.4 ms, spread 15.7 ms.
- [x] MO-1 target met, or missed with the reason written down. Met: 42.4 ms against ≤ 150 ms. OBJECTIVES.md says what that does and does not show.
- [x] `group_by=shape_type` returns counts per label and shape type, and the totals equal the plain counts. Evidence: `docs/evidence/grouping.txt` (0 mismatches over 80 labels, 3,953 = 3,953; invalid value → 400) and `screenshots/chart-by-shape-type.png`.

## Hygiene

- [ ] The first commit holds only these docs; commits after it are small and say what changed and why.
- [ ] No dead code, no commented-out blocks, no stray files in the diff.
- [ ] Everything not finished is listed below with the reason.

## Not finished

(Filled in at the end.)
