# Debt Registry — sample ledger

> This file demonstrates the format contract. P grade comes from the section
> header; each debt has a status field. Active = 'open' or 'open (...)'.

---

## P0 — safety / keys / core path

### D-2026-09-05-014 — sample P0 debt
- **发现时间**: 2026-09-05
- **文件**: `example.md`
- **问题**: demonstrates an active P0 debt
- **状态**: open (P0)
- **预估**: 1 小时

## P1 — correctness debt

### D-2026-09-05-003 — sample active P1
- **发现时间**: 2026-09-05
- **问题**: an open P1 debt shows up in p1_active
- **状态**: open
- **预估**: 2 小时

### D-2026-09-05-007 — sample in-progress P1 (NOT active)
- **发现时间**: 2026-09-05
- **问题**: in-progress must not count as active
- **状态**: in-progress
- **预估**: 30 分钟

### D-2026-09-05-011 — sample deferred P1 (NOT active)
- **发现时间**: 2026-09-05
- **问题**: deferred must not count as active
- **状态**: deferred
- **预估**: 1 小时

## P2 — tech debt

### D-2026-09-05-004 — sample active P2
- **发现时间**: 2026-09-05
- **问题**: an open P2 debt shows up in p2_active
- **状态**: open (未影响门禁)
- **预估**: 1 小时

### D-2026-09-05-005 — sample done P2 (NOT active)
- **发现时间**: 2026-09-05
- **问题**: done must not count as active
- **状态**: done ✓
- **预估**: 30 分钟

---

## 已完成债 (历史)

### D-2026-09-05-FIX1 — sample completed fix
- **修复时间**: 2026-09-05
- **问题**: history entries land in done_recent
- **状态**: done ✓
