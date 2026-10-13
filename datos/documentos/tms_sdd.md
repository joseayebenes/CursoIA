# Track Management Software (TMS) — Software Design Description

Doc. TMS-SDD-001, Issue 3. Company Confidential.

## 1 Scope

This document describes the design of the Track Management Software (TMS) of the coastal
surveillance system. The TMS receives the reports of the surveillance sensors, keeps one
track for each detected target, raises alarms when a target enters a restricted zone and
keeps the operator display (HMI) up to date. The requirements of the TMS are those of the
module SRS_TMS. This issue covers the primary sensor only; the secondary sensor is an open
issue (section 9).

## 2 Definitions

| Term | Meaning |
|---|---|
| Target | An object detected by a sensor. The sensor gives each target a target number. |
| Report | One detection of a target by a sensor: target number and position. |
| Track | The software's record of a target: identifier, position and time of the last report. |
| Stale track | A track that has received no report for the stale timeout (10 s). The target is no longer being detected; operators also call it a "coasting" or "lost" track. |
| Purge cycle | The periodic task that removes stale tracks. |
| Restricted zone | An area in which the presence of a target must be signalled to the operator. |
| Event log | The chronological record of track deletions, alarms and software events. |
| HMI | The operator display and its keyboard. |

## 3 Architecture

The TMS is a single Ada program. It is organised in the following packages:

| Package | Responsibility |
|---|---|
| `Tracks` | Types shared by every package: `Track`, `Track_Id`, `Position`, `Seconds`, and the timing constants. |
| `Clocks` | The time base: seconds since the software started. |
| `Sensor_Input` | Reading and decoding the reports of the primary sensor. |
| `Track_Store` | The table of current tracks: creation, update, deletion and purge of stale tracks. |
| `Zones` | The restricted zones and the test of whether a position is inside one. |
| `Alarms` | Detection of the entry of a track into a restricted zone. |
| `HMI` | The messages to the operator display and the alarm acknowledgement. |
| `Logger` | The event log. |
| `Tms_Main` | The main loop. |

The main loop takes each report from `Sensor_Input`, finds the track of its target in
`Track_Store` (or creates one), updates its position and passes the track to `Alarms`.
`Track_Store` informs the `HMI` of every change in the table. Track deletions and alarms
are written to the event log by `Logger`.

The track table is a fixed array of `Max_Tracks` entries. A track identifier is the index
of its entry, and identifiers are reused: when a track is deleted, its entry becomes free
and the next new target may receive the same identifier.

## 4 Track lifecycle

### 4.1 Creation

When a report arrives for a target number that has no track, `Track_Store.Create` takes
the first free entry of the table, fills it with the target number, the position and the
time of the report, and sends a `TRACK` message to the HMI. The search for a free entry is
linear; with 1000 entries it takes well under a millisecond, so a new track is created and
displayed in the same main loop iteration as its first report, within the 1 s required by
SRS-0003.

If the table is full, the report is ignored and the event is logged. The table size of
1000 tracks satisfies the capacity required by SRS-0011.

### 4.2 Update

A report for a target that already has a track updates its position and the time of its
last report (`Track_Store.Update`), and the new position is sent to the HMI in a `TRACK`
message (SRS-0005, SRS-0040).

### 4.3 Deletion on operator request

The operator may delete any track from the HMI by selecting it and pressing the DEL key.
The HMI sends the request to the TMS, which calls `Track_Store.Delete`. The entry is freed,
a `TRACK_DELETED` message is sent to the HMI (SRS-0044) and the deletion is recorded in the
event log (SRS-0008). The whole sequence takes less than 100 ms, within the 2 s required by
SRS-0006.

### 4.4 Purge of stale tracks

A target that stops being detected leaves behind a track that no longer receives reports.
Keeping such a track on the display for a short time is useful, because the target may be
detected again; keeping it too long misleads the operator.

A track becomes stale when it has received no report for the stale timeout,
`Stale_Timeout` = 10 s. The main loop runs the purge cycle once per purge period,
`Purge_Period` = 1 s, independently of the arrival of reports. The purge cycle
(`Track_Store.Purge_Stale`) examines every entry of the table and deletes each stale
track exactly as an operator deletion does: `TRACK_DELETED` message to the HMI and record
in the event log.

The worst-case time from the moment a track becomes stale to its removal from the display
is therefore one purge period plus the HMI update time, below 1.1 s. This is within the 2 s
required by SRS-0004. Issue 2 of this document used a purge period of 2 s; it was reduced
to 1 s in Issue 3 to leave margin against that requirement.

## 5 Alarms

### 5.1 Restricted zones

In this issue the restricted zones are two rectangles in sensor coordinates, defined in
`Zones`. A later issue will read them from the site configuration.

| Zone | X (m) | Y (m) |
|---|---|---|
| Harbour entrance | 1000 to 2000 | -500 to 500 |
| Fuel terminal | -3000 to -2500 | 0 to 800 |

### 5.2 Raising an alarm

After each report, the main loop passes the track to `Alarms.Check`, which compares the
zone status of the track with its status at the previous report. When a track that was
outside every restricted zone is now inside one, an alarm is raised: an `ALARM` message is
sent to the HMI (SRS-0041) and the alarm is recorded in the event log (SRS-0009).

The latency budget of an alarm, from the report to the alarm on the display, is:

| Step | Budget |
|---|---|
| Report decoding and zone check in the main loop | 100 ms |
| `ALARM` message to the HMI | 200 ms |
| Display of the alarm | 100 ms |
| **Total** | **400 ms** |

The total is within the 500 ms required by SRS-0007.

### 5.3 Acknowledgement

An alarm stays on the display, in red, until the operator acknowledges it with the F2 key
(SRS-0010). Acknowledging an alarm does not delete the track.

## 6 Event log

Every event is written as one line with the time since the software started, in seconds,
and a text: `[ 12.500000000 s] Track 7 deleted`. The log records every track deletion,
whether requested by the operator or caused by the purge cycle (SRS-0008), and every alarm
(SRS-0009). The log is written to the standard output of the program and collected by the
platform.

## 7 HMI interface

The messages between the TMS and the HMI are defined in the Interface Control Document,
TMS-ICD-002. The TMS sends:

| Message | When | Requirement |
|---|---|---|
| `TRACK` | A track is created or updated | SRS-0040 |
| `TRACK_DELETED` | A track is deleted, by the operator or by the purge cycle | SRS-0044 |
| `ALARM` | A track enters a restricted zone | SRS-0041 |
| `HEARTBEAT` | Every 1 s, so that the HMI can detect a TMS failure | SRS-0042 |

`HEARTBEAT` is not implemented in this issue (open issue OI-3).

## 8 Performance and capacity

| Function | Required | Designed | Requirement |
|---|---|---|---|
| Creation of a new track | 1 s | same loop iteration | SRS-0003 |
| Update of a track | 1 s | same loop iteration | SRS-0005 |
| Deletion on operator request | 2 s | < 100 ms | SRS-0006 |
| Deletion of a stale track | 2 s | < 1.1 s | SRS-0004 |
| Alarm on entering a restricted zone | 500 ms | 400 ms | SRS-0007 |
| Simultaneous tracks | 1000 | 1000 | SRS-0011 |

## 9 Open issues

| Id | Issue | Requirement |
|---|---|---|
| OI-1 | The interface of the secondary sensor is not defined yet; the sensor supplier will deliver it. Until then, only the primary sensor is supported. | SRS-0002 |
| OI-2 | The recovery of the tracks after a restart is not designed. After a restart the track table is empty and tracks are created again as reports arrive. | SRS-0012 |
| OI-3 | The `HEARTBEAT` message is to be implemented in Issue 4. | SRS-0042 |
