# I3: RCSP to routing contract

The repository-wide I1–I8 schema and output table is in
[interfaces.md](./interfaces.md).

M3 (`src/rcsp`) communicates RCSP solutions to M8 (`src/routing`) through the
WS2 output file `rcsp_sensitivity.csv`. M8 must not import RCSP types or modules.
The WS6 orchestration script owns file loading and converts each optimal row to
the intermediate routing type `RouteReference(name, path)`.

## CSV fields consumed by WS6

| Field | Meaning |
|---|---|
| `resource_limit` | Resource/time limit; an empty value denotes an unbounded solve. |
| `status` | Only rows whose value is `Optimal` become route references. |
| `optimal_path` | Hyphen-delimited node sequence, for example `O-A-B-T`. |

The reference name is `RCSP_limit_<value>`; an empty limit is named
`RCSP_limit_unbounded`. Invalid route strings or missing required columns raise
a descriptive `ValueError`. If the file itself is absent, WS6 warns and
continues without RCSP references.

`src.routing.parse_route_path` parses the route string to a tuple of node IDs.
`run_routing_experiment` validates each reference's source/target and verifies
that each consecutive node pair is a network edge. An invalid path raises a
`ValueError` naming the route reference.

Each accepted RCSP route is evaluated for every test slot/day. Its actual score
is summed from test observations and its regret is calculated against the
Oracle actual-time route, just as for other route methods. The `method_family`
value for these results is `rcsp`.
