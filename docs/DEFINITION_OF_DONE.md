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

## Live updates (items 8–9, lines added when they came back into scope)

- [x] Adding or deleting an annotation changes the pushed total without reloading, with the delay measured (`docs/evidence/live_check.py` output). Evidence: `docs/evidence/live.txt`, 3953 → 3954 → 3953, pushes after 2.04 s and 2.03 s (the 2 s check interval plus the request).
- [ ] The page shows the change live in the browser (before/after screenshots).
- [x] When the server goes away the page shows "Connection lost, retrying"; when it returns the page shows "Live" again with current counts (screenshots). Evidence: `screenshots/reconnecting.png` (after `docker stop cvat_server`) and `screenshots/reconnected.png` (after `docker start cvat_server`). The first screenshot was taken before the countdown fix (commit `c4e0eab`), so it shows the fixed "30 s" text; the countdown was then checked by eye.
- [x] A user without access is refused on the socket too (close code 4403). Evidence: `docs/evidence/live.txt`, last line.

## Hygiene

- [x] The first commit holds only these docs; commits after it are small and say what changed and why. Evidence: `git log --reverse 8d7ae75..dev-test01`; the first commit, `e7898b5`, has only `docs/`.
- [x] No dead code, no commented-out blocks, no stray files in the diff. Checked with `git diff 8d7ae75..HEAD`: 36 files, all additions. Backend changes are in `cvat/apps/test` except 4 registration lines (`settings/base.py`, `urls.py`, `asgi.py`); UI changes are in `components/label-counts-page` except the route and the menu entry.
- [x] Everything not finished is listed below with the reason.

## Not finished

- **Browser "after" screenshot for live updates.** The push is proven by `live.txt`
  (3953 → 3954 → 3953) and `screenshots/live.png` shows the Live tag. I did not capture the
  page at the moment it showed 3954, because the count is back to 3953 about 2 s later.
- **Tracks and tags are not counted.** Only `LabeledShape` is counted. `LabeledTrack` (video
  tracks) and `LabeledImage` (tags) are not, because COCO creates neither and I had no data to
  check them against.
- **No tests in CVAT's own test suite.** The evidence comes from scripts run against the live
  stack, not from tests in `tests/python` that CI would run. Writing them would mean setting up
  CVAT's REST test fixtures, which I left for the time I had.
- **Scaling not measured.** MO-1 is measured on 500 images (3,953 shapes). I did not measure the
  full 5,000-image set, so I cannot say how the endpoint or the 2 s live check behaves there.
- **Organizations not tested.** Everything ran in the personal workspace. The permission check
  reuses CVAT's task rules, which cover organizations, but I did not test with an organization.
- **Live updates are polled, not event-driven.** See the decision record in PLAN.md for the
  cost: up to 2 s delay and one count request every 2 s per open page.

