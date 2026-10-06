# Objectives

## Machine

| Item | Value |
|------|-------|
| Host | GitHub Codespace, 4-core machine type (raw output: `docs/evidence/machine.txt`) |
| CPU | AMD EPYC 7763, 4 vCPUs available |
| RAM | 15 GiB total, 8.8 GiB available while the CVAT stack was running |
| OS | Ubuntu 24.04.5 LTS |
| CVAT commit | `8d7ae755c5b8de82e8711756b35c0207655ef1ae` |
| Dataset | COCO 2017 val, first 500 images by file name: 3,541 COCO annotations, imported by CVAT as 3,953 shapes, one task (id 1) |

## MO-1 — Label count endpoint latency

| Field | Entry |
|-------|-------|
| What is measured | Total time for `GET` on the label-count endpoint for the COCO task, from request sent to last byte received. |
| How | `curl -s -o /dev/null -w '%{time_total}\n'` from inside the Codespace, with a token for the task owner. 1 warm-up request, then 5 measured runs. The script and raw output are saved in `docs/evidence/`. |
| Target | Median of 5 runs at or below 150 ms. Spread (max − min) reported. |
| Why this number | The page makes this single call before drawing anything. CVAT's own task page already makes several API calls, so a chart that adds more than about 150 ms would be noticeable. The query is one `GROUP BY` over indexed foreign keys, so missing this target would point to a query problem, not to the dataset size. |
| Conditions | Local Docker stack in the Codespace, the COCO task above, no other requests running, server already warm. |
| Not included | Browser rendering time, the first request after a container restart, and the `group_by=shape_type` variant (measured separately if time allows). |

## Results

Raw output: `docs/evidence/mo1.txt` (measured 2026-10-06 17:07 UTC).

| Run | 1 | 2 | 3 | 4 | 5 |
|-----|---|---|---|---|---|
| Time (ms) | 36.1 | 34.7 | 42.4 | 50.4 | 43.7 |

**Median 42.4 ms, min 34.7 ms, max 50.4 ms, spread 15.7 ms. Target (≤ 150 ms) met.**

What this does and does not show:

- At 3,953 shapes the target was met with about 3.5× headroom. At this data size it was not
  demanding, so it confirms the query is not wasteful. It does not show how the endpoint scales.
- The spread (15.7 ms) is about a third of the median. On a shared Codespace, five runs are
  enough to say "well under 150 ms" but not to compare small optimisations.
- The time includes Traefik routing, token authentication and the OPA permission call, not only
  the database query. I did not separate them, so I cannot say which part dominates.
