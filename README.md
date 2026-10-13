# A3-PS001-TC185

Behavior-based early warning detector for a controlled Android test environment.

## What it does

- Monitors rewrite and rename file events in a rolling time window
- Flags suspicious rapid rewrite+rename behavior
- Generates an alert object with event counts and trigger time
- Stops only the controlled test workload object tied to the detector

## Quick test

```bash
python -m unittest discover -s tests -q
```
