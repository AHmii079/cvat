# Objectives

## Machine

| Item | Value |
|------|-------|
| Host | GitHub Codespace (filled in from `lscpu`, `free -h`, `/etc/os-release`) |
| CPU | TBD |
| RAM | TBD |
| OS | TBD |
| CVAT commit | `8d7ae755c5b8de82e8711756b35c0207655ef1ae` |
| Dataset | COCO 2017 val, TBD images / TBD annotations in one task |

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

(Raw output pasted here after measuring.)
