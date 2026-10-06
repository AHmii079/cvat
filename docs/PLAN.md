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
  I will reuse `TaskPermission.create_scope_view`, so access follows the existing task rules
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

## Changes during the work

(Filled in as they happen, with the reason.)
