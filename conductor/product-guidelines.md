# Product Guidelines: OpenSCAD MCP Plugin

## Prose & Communication Style
- **Tone**: Conversational and helpful. Tool responses should be friendly, use clear explanations, and avoid jargon where possible. Suitable for makers and hobbyists who may not have deep CAD experience.
- **Example**: Instead of `"Rendering complete. Output: /tmp/foo.png"`, prefer `"Here's your isometric preview of the bracket! The model rendered cleanly with no warnings. Preview saved to /tmp/foo.png."`
- **Technical Precision**: While the tone is friendly, all measurements, coordinates, and engineering values must be precise and unambiguous.

## Output Conventions
1. **Units**: Always include units in all dimensional output. Default to metric (millimeters). When relevant, provide inch equivalents in parentheses (e.g., `6.35mm (1/4")`).
2. **Color-Coding in Renders**: Use consistent, semantic color assignments:
   - `gray` / `darkgray` — Hardboard/panel faces
   - `burlywood` — Pine joining blocks, cleats, and support structures
   - `red` — Error indicators, collision highlights, dimension annotations
   - `green` — Success indicators, clearance zones
3. **Structured + Human-Readable**: Every tool response should include both:
   - A human-readable summary (conversational text)
   - Machine-parseable structured data (JSON) for downstream tooling, where applicable
4. **File Paths**: Every tool response that generates artifacts must include the absolute file path(s) to those artifacts.

## Error Handling
- **Fail Fast**: When an error occurs (missing file, invalid geometry, OpenSCAD compilation failure), stop immediately and return a clear, actionable error message.
- **Error Format**: Errors should include: (1) what went wrong, (2) the likely cause, and (3) a suggested fix.
- **No Partial Results on Error**: Do not attempt to produce partial or degraded output when a critical step fails. Report the failure cleanly.

## UX Principles
1. **Inline Previews**: Preview images must always be returned inline (base64-encoded) in the MCP response payload, not just saved to disk. This ensures the AI assistant can display them directly in the conversation.
2. **Artifact Paths Always Visible**: Every generated file (SCAD, STL, DXF, SVG, PNG) must have its absolute path reported in the response text.
3. **Metric-First Dimensioning**: All dimension annotations default to metric (mm). An `imperial` flag or parameter should be available to switch to inches when requested.
4. **Deterministic Behavior**: Given the same input SCAD file and parameters, every tool must produce identical output. No randomized behavior.
5. **Non-Destructive**: Tools should never overwrite input files without explicit confirmation or a separate output path.
