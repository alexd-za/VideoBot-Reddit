# MCP routing

## Preferred tool split

Use the Fusion MCP server for:

- live document state;
- sketches, parameters, features, bodies, and components;
- joints and assembly relationships;
- interference and motion inspection;
- save, version, and export operations.

Use the local Guardian scripts for:

- deterministic STL topology checks;
- dimension and volume acceptance ranges;
- repeatable JSON and Markdown reports;
- before/after regression comparison;
- batch auditing of several exported parts.

## Tool discovery

MCP tool names and schemas may change. Before acting:

1. inspect connected MCP servers;
2. identify the Fusion server;
3. inspect its available tools;
4. map the required operation to the current tool schema;
5. avoid guessing unavailable operations.

## Fallbacks

- If no semantic inspection tool exists, mark that item `NOT VERIFIED`.
- If no mesh export tool exists, request manual STL export.
- If no interference tool exists, do not infer clearance from a screenshot.
- If the active design cannot be safely duplicated, get explicit approval before modifying it.
