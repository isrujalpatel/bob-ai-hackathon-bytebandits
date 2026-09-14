# Problem Statement: Container Congestion at the Port of Los Angeles

## Who Is Affected

Port operations supervisors, terminal operators, vessel scheduling teams, and shipping-line dispatchers at large container terminals worldwide. Indirectly: every manufacturer, retailer, and consumer whose goods move through a major container port.

## The Reality of Manual Port Scheduling

Today's berth and crane allocation at most major terminals is managed in spreadsheets and static daily schedules produced the night before. The workflow is:

1. A planner receives expected vessel ETAs (often updated within hours of arrival).
2. They manually match each vessel to an available berth based on vessel length, terminal assignment, and crane availability.
3. Congestion is discovered **reactively** — when a vessel reports it is anchorage-bound because its assigned berth is still occupied.

By the time a congestion signal reaches the planning team, rerouting or rescheduling decisions come too late: the vessel is already queuing offshore, accruing demurrage charges, and blocking berth access for the next arrival.

## Quantified Pain

The 2021 Los Angeles/Long Beach congestion event is the clearest modern example:

- **108 vessels** anchored offshore simultaneously at peak (November 2021)
- Ships waited an average of **17 days** before berthing
- Estimated supply-chain cost: **> $10 billion** in delayed goods, demurrage fees, and knock-on inventory shortfalls
- Dwell time for containers in yard doubled; rail and trucking networks downstream backed up for months

This was not primarily a capacity problem — the port complex has theoretical throughput for the volume involved. It was a **coordination and visibility problem**: no system connected real arrival volumes to proactive allocation decisions in a shift-supervisor-readable format.

## Why Existing Approaches Fail

| Approach | Why It Falls Short |
|---|---|
| Static daily spreadsheet | No real-time update when ETAs shift; no forward-looking demand model |
| Reactive gate/berth monitoring | Detects congestion after it has already formed; too late to reroute |
| Commercial TOS (Terminal Operating Systems) | Expensive, single-terminal scope, no multi-vessel horizon view |
| AIS dashboards (e.g., MarineTraffic) | Shows where vessels are *now*, not which berths will be *over-capacity* in 12 h |

## Why It Matters Now

Global container throughput is projected to grow 4% per year through 2030. Without proactive planning tools, every demand spike — post-holiday restocking, supply-chain disruption, weather events — risks a repeat of 2021. Port operators need a system that tells them **which time windows will be over-capacity before vessels are already waiting** and hands them an actionable plan in plain language.
