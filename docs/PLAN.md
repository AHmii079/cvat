# Plan — Annotation Analytics

Base commit: `8d7ae755c5b8de82e8711756b35c0207655ef1ae` (`develop` of my fork AHmii079/cvat, 6 Oct 2026).
Branch: `dev-test01`. Runtime: GitHub Codespace (specs in OBJECTIVES.md), because my
laptop has 8 GB RAM and CVAT needs about 8 GB free on its own.

## What I found before writing code

- A drawn box is a `LabeledShape` (`cvat/apps/engine/models.py`). Its class is
  `Annotation.label`, a foreign key to `Label`, whose `name` is the class name.
- Shapes belong to a `Job`, not a task. The path is
  `Task ← Segment.task ← Job.segment ← LabeledShape.job`, and then `LabeledShape.label → Label.name`.
- Labels can belong to the task *or* to its project, so I filter shapes by
  `job__segment__task_id`, never by `label__task`.
- Every DRF view must declare `iam_permission_class`. `PolicyEnforcer`
  (`cvat/apps/iam/permissions.py`) asserts on it and asks that class which OPA checks to run.
  I will reuse `TaskPermission`, so access follows the existing task rules
  instead of a check I write myself.
- `cvat-ui` already ships `chart.js` + `react-chartjs-2`, and `core.server.request` sends
  CVAT's own auth. No new dependencies are needed.

## Order and time (8 h budget)

| # | Step | Time |
|---|------|------|
| 0 | This plan, Objectives draft, Definition of Done; commit before any code | 0:30 |
| 1 | `cvat/apps/test` app: endpoint counting shapes per label with one `GROUP BY` query | 1:15 |
| 5 | Permission class reusing `TaskPermission` (view scope); prove 401 / 403 / 200 with curl | 0:45 |
| 2–4 | UI route `/tasks/:tid/label-counts`, bar chart, empty state, error state, link from task page | 1:45 |
| 6 | Measure MO-1: 5 runs, raw output saved | 0:45 |
| 7 | Filter: `?group_by=shape_type` (rectangle / polygon / mask) | 0:45 |
| — | Finish docs with evidence, rehearse, record | 1:15 |
| | Buffer for builds and surprises | 1:00 |

I do item 5 straight after item 1. An endpoint that leaks counts is not "done", even if the
floor is items 1–4.

## Decided up front

- Counted: `LabeledShape` only, excluding skeleton child points (`parent` not null) so a
  skeleton counts once. COCO import creates shapes only. Tracks and tags are listed as not covered.
- Counts are computed at request time with the ORM, not stored. Reason: CVAT writes
  annotations with `bulk_create`, which skips model signals, so a stored counter would go stale silently.

## Planned skips

- Items 8–9 (live WebSocket updates and reconnect). CVAT does not ship Django Channels.
  Adding it means ASGI routing plus a channel layer, which is hours of risk for bonus items.
  I return to them only if items 1–7 are done and documented with at least 2 hours left.

## Item 7 — why group by shape type

I chose shape type over filtering by job or by frame range. COCO mixes two kinds of annotation for
the same class: object outlines and "crowd" regions. They are imported as polygons and masks, and
they are used differently when training (instance outlines versus regions to ignore or segment).
A plain count hides that mix, which matters when deciding if a class has enough usable examples.
It is also cheap: one more column in the same `GROUP BY`, no extra query.
The result confirmed the reason: task 1 has 3,916 polygons and 37 masks, and no rectangles.

## Changes during the work

- **Permission scope.** I planned `TaskPermission.create_scope_view` (the `view` scope). I used
  `view:annotations` instead, through `TaskPermission.create_base_perm`, because the endpoint
  reveals annotation data, not just task metadata. CVAT's rules list both scopes.
- **Runtime fixes, not code changes.** Containers in the Codespace could not reach each other
  (server → database timed out). The cause was two iptables backends: bridge traffic was filtered
  by rules Docker had not written. Fixed with `sysctl net.bridge.bridge-nf-call-iptables=0` and
  `iptables-legacy -P FORWARD ACCEPT`. Cost: about 15 minutes.
- **Counts do not equal COCO instances.** The task has 3,541 COCO annotations but 3,953 shapes.
  A COCO object whose outline has several parts is imported as several polygons. I changed the
  correctness check to compare against expected *shapes*, and it matches on all 80 labels
  (`docs/evidence/counts.txt`). The page reports shapes, and says "annotations" in the CVAT sense.
- **Chart layout.** With 80 labels, Chart.js hid every other name, and then the card squeezed
  the rows together. Fixed in two small commits after seeing it in the browser.
- **Items 8–9 back in scope (decided at about 2 h of work, items 1–7 done).** The skip assumed
  WebSocket support meant adding Django Channels. Reading CVAT showed it already runs Django under
  uvicorn (`supervisord/server.conf`, `cvat/asgi.py`) with the `websockets` package installed,
  and its nginx already forwards the `Upgrade` header. So a WebSocket route needs only a small
  ASGI wrapper, not a new framework. Plan for 8–9, about 1.5 h:
  1. ASGI wrapper in `cvat/apps/test/live.py`, hooked into `cvat/asgi.py`, serving
     `/api/tasks/{id}/label-counts/live`.
  2. Each tick, the wrapper calls the existing REST endpoint internally with the socket's own
     cookies, so login, permissions and counting are reused, not copied. It pushes only when the
     result changed, and closes with 4401/4403/4404 when access fails.
  3. The page subscribes, updates the chart in place, shows the connection state, and reconnects
     with backoff (1 s, 2 s, 4 s … up to 30 s), refetching once reconnected.

