# Example: Local Events Board

**Starting point:** "I have a detailed spec"

This walkthrough follows someone building an events board that pulls from an external API and displays events on a map. They've written a spec with clear requirements. It shows how DOE handles external data, deterministic execution scripts, and spec-driven development.

---

## The idea

> "Pull events from the Eventbrite API. Show them on a Leaflet map. Filter by category and date range. Click an event marker to see details — title, description, time, venue."

This is a proper specification. There's a named data source (Eventbrite API), a named technology (Leaflet maps), specific features (filter by category, filter by date, click for details), and a clear picture of the end result. When you start with this much clarity, DOE can move fast.

## How you'd start

Because there's a written spec, the first step is turning it into a directive — a file in `directives/` that Claude can reference throughout the build. You paste your spec and Claude saves it as `directives/events-board-spec.md`, adding structure: inputs, outputs, edge cases, verification criteria.

Claude reads the directive and creates a detailed plan in `.claude/plans/events-board.md`:

1. Execution script for API import — fetch events from Eventbrite, cache locally, output clean JSON
2. Data validation — ensure events have required fields (title, date, location coordinates)
3. Map rendering — display a Leaflet map with event markers
4. Category filter — dropdown or tag buttons to filter events by type
5. Date range filter — select a start and end date, hide events outside the range
6. Event detail panel — click a marker, see the full event details
7. Empty and error states — what happens when the API is down, when no events match the filters
8. Polish — loading indicators, responsive layout, map zoom behaviour

Step 1 is the critical DOE moment: a dedicated execution script. Not inline code, not Claude improvising an API call — a proper Python script in `execution/` that handles the Eventbrite API reliably.

## What a session looks like

### Session 1: The execution script

Claude starts with `execution/import_events.py`. Before writing a single line, it checks `learnings.md` for any existing API patterns — this is progressive disclosure, where Claude automatically loads relevant context based on what it's about to do. If the project has imported from external APIs before, those patterns (caching strategy, error handling, rate limiting) get applied to the new script.

The execution script handles:
- Authentication (API key from `.env` — never hardcoded)
- Pagination (Eventbrite returns events in pages of 50)
- Caching (saves raw responses to `.tmp/` so you don't hit the API repeatedly during development)
- Validation (checks that every event has coordinates, a title, and a date)
- Output (writes a clean `src/data/events.json` file)

The contract for this step:

```
1. [ ] Execution script for API import
   Contract:
   - [ ] [auto] Script exists. Verify: file: execution/import_events.py exists
   - [ ] [auto] Script runs without error. Verify: run: python3 execution/import_events.py --dry-run
   - [ ] [auto] Output has required fields. Verify: run: python3 tests/validate_events.py
```

Notice the `--dry-run` flag. The execution script supports running against cached data instead of hitting the live API — so tests can verify the script works without spending API credits every time.

After the script is built and passes its contract, Claude runs it once for real (after confirming with you, since it uses API credits). The result: 200 events, all validated, saved to `events.json`.

### Session 2: The map

You run `/stand-up`. Claude reports: "Execution script complete. 200 events imported and validated. Next: map rendering."

With clean data in hand, Claude builds the Leaflet map. Each event becomes a marker at its latitude/longitude. The directive says "Leaflet map" specifically, so Claude doesn't second-guess the technology choice — it follows the spec.

The map contract includes both automated and manual checks:

```
3. [ ] Map rendering
   Contract:
   - [ ] [auto] Map container exists. Verify: html: index.html has #event-map
   - [ ] [auto] Markers placed from data. Verify: run: node tests/map-markers.test.js
   - [ ] [manual] Map loads at a sensible zoom level — all events visible without scrolling
```

The automated tests pass. The manual check will wait until the end of the feature — Claude keeps building without stopping for approval.

### Session 3: Filters and details

Claude builds the category filter, the date range filter, and the event detail panel. During development, the API returns an event with a category value Claude's code doesn't expect — `"category": null` instead of a string. The filter crashes.

This is where self-annealing kicks in. Claude:

1. Reads the full error to understand what happened
2. Diagnoses why — the API doesn't guarantee a category field
3. Fixes the filter to handle null categories (groups them under "Uncategorised")
4. Adds a validation rule to the execution script so this edge case is caught at import time
5. Logs the finding to `learnings.md`:

> Eventbrite API: category field can be null. Handle as "Uncategorised" in filters, add null check to import validation.

Next time anyone imports from this API — or any API — that learning is available. The system got smarter from one bug.

## What DOE gives you

This walkthrough shows four DOE concepts with a spec-driven project:

**The directive meant Claude followed your spec, not its own interpretation.** When the spec said "Leaflet map," Claude used Leaflet — it didn't substitute a different library because it thought that one was better. When the spec said "filter by category and date," Claude built exactly those two filters, not five filters it thought would be nice. The directive is the authority.

**The execution script is deterministic.** `python3 execution/import_events.py` does the same thing every time: fetches events, validates them, outputs JSON. There's no AI reasoning in this path — no chance of hallucination or inconsistency. If the output is wrong, you fix the script. The fix works forever.

**Progressive disclosure loaded the right context automatically.** Claude didn't need to be told "check for API patterns before writing the import script." The trigger in CLAUDE.md fired automatically: "Importing external data? Check learnings.md for API patterns." The relevant knowledge surfaced without you asking for it.

**Self-annealing turned a bug into permanent knowledge.** The null category bug wasn't just fixed — it was logged, and the validation was tightened so the same class of bug can't happen again. Every failure makes the import script more robust. After a few rounds of this, the execution script handles edge cases you never would have anticipated.

---

This is DOE with external dependencies: a reliable execution layer between your app and the outside world, a directive keeping the build on spec, and a self-improving system that gets better with every bug it encounters.
