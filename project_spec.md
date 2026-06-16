# Product Counting Application (POC/MVP)
## YOLO + ByteTrack Based Loading/Unloading Monitoring System

---

# 1. Problem Statement

## Business Objective

Develop a real-time computer vision application that monitors multiple CCTV streams across a factory and automatically detects product loading and unloading activities.

Once a loading or unloading operation is detected, the system should:

1. Identify the operation type (Loading / Unloading)
2. Start a counting session automatically
3. Count products moving through a predefined counting zone
4. Display real-time counts on a central dashboard
5. Maintain historical logs and audit records
6. Generate operational metrics for supervisors and management

---

## Current Challenges

Manual counting introduces:

- Human error
- Missed counts
- Delayed reporting
- Lack of operational visibility
- No historical analytics
- Inconsistent shift-wise reporting

---

## Proposed Solution

Deploy an AI-powered vision system using:

- YOLO Object Detection
- ByteTrack Object Tracking
- Virtual Line-Crossing Logic
- Event-Based Loading/Unloading Detection

The system will continuously monitor CCTV streams and automatically count products entering or exiting designated areas.

---

## Scope of MVP

### Included

- Multi-camera support
- Real-time video processing
- Automatic loading/unloading detection
- Product counting
- Dashboard visualization
- Session logging
- Historical reports

### Excluded (Future Enhancements)

- ERP integration
- SAP integration
- Vehicle OCR
- Product barcode validation
- Cross-camera re-identification
- Predictive analytics

---

# 2. Recommended MVP Architecture

## High-Level Architecture

```text
                ┌──────────────────┐
                │ CCTV Cameras     │
                │ RTSP Streams     │
                └────────┬─────────┘
                         │
                         ▼

            ┌──────────────────────────┐
            │ Video Processing Service │
            │                          │
            │ YOLO Detection           │
            │ ByteTrack Tracking       │
            │ Activity Detection       │
            │ Counting Engine          │
            └──────────┬───────────────┘
                       │
                       ▼

            ┌──────────────────────────┐
            │ Event Processing Service │
            │                          │
            │ Session Management       │
            │ Metrics Calculation      │
            │ Count Aggregation        │
            └──────────┬───────────────┘
                       │
                       ▼

            ┌──────────────────────────┐
            │ Database                 │
            │                          │
            │ Cameras                  │
            │ Sessions                 │
            │ Count Events             │
            │ Logs                     │
            └──────────┬───────────────┘
                       │
                       ▼

            ┌──────────────────────────┐
            │ Dashboard                │
            │                          │
            │ Live Streams             │
            │ Counts                   │
            │ Metrics                  │
            │ Reports                  │
            └──────────────────────────┘
```

---

## Camera Processing Pipeline

```text
RTSP Stream
      │
      ▼
Frame Extraction
      │
      ▼
YOLO Detector
      │
      ▼
ByteTrack Tracker
      │
      ▼
Activity Detection
      │
      ▼
Loading / Unloading Classification
      │
      ▼
Line Crossing Detection
      │
      ▼
Count Update
      │
      ▼
Dashboard Update
```

---

# 3. Automatic Loading/Unloading Detection

## Objective

Automatically determine when a loading or unloading operation starts and ends without human intervention.

---

## Detection Entities

First try with pretained YOLO model to detect the products. If failed then YOLO should be trained to detect:

```text
Product
Forklift
Worker
Truck/Wagon
```

---

## Operational Zones

Each camera configuration should contain:

```text
Truck Zone
Loading Area
Product Buffer Area
Counting Line
```

---

## Loading Detection Logic

### Start Loading

Loading session begins when:

```text
Truck detected

AND

Forklift detected near truck

AND

Products moving toward truck

AND

Continuous movement detected for X seconds
```

Example:

```text
Truck Present = TRUE

Forklift Present = TRUE

Movement Direction:
Warehouse → Truck

Duration > 10 sec
```

Result:

```text
Session Type = LOADING
Status = ACTIVE
```

---

## Unloading Detection Logic

### Start Unloading

Unloading session begins when:

```text
Truck detected

AND

Products moving away from truck

AND

Forklift activity detected

AND

Movement sustained for X seconds
```

Example:

```text
Truck Present = TRUE

Movement:
Truck → Warehouse

Duration > 10 sec
```

Result:

```text
Session Type = UNLOADING
Status = ACTIVE
```

---

## Session End Logic

Session automatically closes when:

```text
No product movement detected

AND

No forklift activity detected

FOR

5 minutes
```

Result:

```text
Status = COMPLETED
```

---

# 4. Recommended Technology Stack

## Video Processing Service

### Responsibility

- Stream ingestion
- Detection
- Tracking
- Counting

### Technology

```text
Python 3.12+
OpenCV
YOLOv11
ByteTrack
NumPy
FastAPI
PyTorch
```

---

## Event Processing Service

### Responsibility

- Session management
- Aggregation
- Business rules

### Technology

```text
Node.js
Express.js
TypeScript
```

---

## Real-Time Communication

### Responsibility

- Push live updates to dashboard

### Technology

```text
Socket.IO
WebSockets
```

---

## Database

### Responsibility

- Persistent storage

### Technology

```text
MongoDB
```

Collections:

```text
cameras
camera_configurations
sessions
count_events
activity_events
system_logs
users
```

---

## Dashboard Frontend

### Responsibility

- Monitoring
- Analytics
- Reporting

### Technology

```text
Angular
Angular Material
RxJS
Socket.IO Client
Chart.js
```

---

## Containerization

```text
Docker
Docker Compose
```

Future:

```text
Kubernetes
```

---

# 5. Counting Logic

## Core Principle

The counting mechanism is deterministic.

Counting depends on:

```text
Tracked Object ID
+
Direction of Motion
+
Line Crossing Event
```

---

## Virtual Counting Lines

Recommended:

```text
Line A
Line B
```

---

### Loading Direction

```text
A → B
```

Count:

```text
+1
```

---

### Unloading Direction

```text
B → A
```

Count:

```text
+1
```

(Unloading count maintained separately)

---

## Why Dual-Line Counting

Single-line counting may fail when:

```text
Object pauses
Object reverses
Object oscillates
```

Dual-line counting provides:

```text
Higher accuracy
Direction validation
Reduced false counts
```

---

## Tracking Logic

Example:

```text
Track ID = 101
```

Path:

```text
Crosses Line A
Then Line B
```

Result:

```text
Count Product Once
```

---

## Duplicate Prevention

Store:

```text
Track ID
Session ID
Count Status
```

Example:

```json
{
  "track_id": 101,
  "session_id": "LOAD_20260616_001",
  "counted": true
}
```

Track cannot be counted again.

---

## Count Event Structure

```json
{
  "event_id": "EVT001",
  "camera_id": "CAM01",
  "session_id": "LOAD001",
  "track_id": 101,
  "direction": "LOADING",
  "timestamp": "2026-06-16T10:05:12Z"
}
```

---

# 6. Dashboard Specification

## Objective

Provide a centralized monitoring interface for operations teams.

---

# Dashboard Layout

## Top Summary Section

Display:

```text
Total Cameras Online
Active Sessions
Loading Sessions
Unloading Sessions
Today's Total Count
System Health
```

Example:

```text
Online Cameras: 12
Loading Sessions: 3
Unloading Sessions: 2
Products Counted Today: 18,540
```

---

# Live Camera Monitoring Grid

## Camera Card

Each camera tile should display:

```text
Live Video Stream
Camera Name
Camera Status
Session Status
Current Count
Operation Type
Last Activity Timestamp
```

Example:

```text
CAM-01

LIVE

Loading

Current Count: 245
```

---

## Stream Controls

For each stream:

```text
Mute Audio
Unmute Audio
Fullscreen
Snapshot Capture
Refresh Stream
Pause Stream View
Reconnect Stream
```

---

## Stream Status Indicators

```text
ONLINE
OFFLINE
BUFFERING
PROCESSING
ERROR
```

Color coded.

---

# Session Monitoring Panel

Display active sessions.

Columns:

```text
Session ID
Camera
Operation Type
Start Time
Duration
Current Count
Status
```

---

# Count Metrics Panel

Per Camera:

```text
Current Session Count
Today's Count
Average Count Per Hour
Maximum Count Rate
Minimum Count Rate
```

---

## Plant Level Metrics

Display:

```text
Total Products Loaded Today
Total Products Unloaded Today
Shift Wise Counts
Hourly Trends
Camera Wise Distribution
```

---

# Event Timeline

Real-time event feed.

Examples:

```text
10:05:12 Loading Started
10:05:18 Product Counted
10:05:20 Product Counted
10:05:24 Product Counted
10:30:05 Loading Completed
```

---

# Logs Module

## System Logs

Capture:

```text
Camera Connected
Camera Disconnected
Stream Failure
Model Restart
Session Start
Session End
Count Correction
Configuration Change
```

---

## AI Logs

Capture:

```text
Loading Detection
Unloading Detection
Count Event
Tracking Failure
Detection Failure
Low Confidence Detection
```

---

## Search Filters

```text
Date Range
Camera
Session
Operation Type
Log Type
Severity
```

---

# Historical Reports

Reports should support:

```text
Daily
Weekly
Monthly
Custom Date Range
```

---

## Export Formats

```text
CSV
Excel
PDF
```

---

# User Roles

## Administrator

Permissions:

```text
Camera Configuration
User Management
System Configuration
Model Configuration
Report Access
```

---

## Supervisor

Permissions:

```text
View Streams
View Counts
View Reports
View Logs
```

---

## Operator

Permissions:

```text
View Dashboard
View Active Sessions
View Counts
```

---

# MVP Success Criteria

The MVP shall be considered successful if it achieves:

```text
Detection Accuracy ≥ 95%

Tracking Stability ≥ 95%

Counting Accuracy ≥ 98%

Real-Time Dashboard Latency ≤ 2 Seconds

Automatic Session Detection Accuracy ≥ 90%

Multi-Camera Concurrent Processing Supported
```