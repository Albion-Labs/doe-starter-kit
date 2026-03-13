# Example: Recipe Book App

**Starting point:** "I'm making it up as I go"

This walkthrough follows someone building a simple recipe app. They have an idea but no plan — just a sentence in their head. It shows how DOE turns a vague idea into a structured, trackable build.

---

## The idea

> "I want an app where I can add recipes, search them, and mark favourites. Maybe categories too."

That's it. No spec, no wireframes, no bullet points. Just a loose vision of what the end result should feel like. This is the most common starting point — you know what you want but haven't figured out the details.

## How you'd start

With an idea this vague, the first move is `/scope`. This runs a conversational scoping session where Claude asks questions to turn your fuzzy idea into a concrete brief.

The conversation might go something like this:

- **Claude:** Who's using this — just you, or will other people add recipes too?
- **You:** Just me. It's a personal thing.
- **Claude:** Web app, or something you'd run locally on your computer?
- **You:** Web app. I want to open it in a browser.
- **Claude:** When you say "categories" — do you mean fixed categories like "Breakfast, Lunch, Dinner" or tags you create yourself?
- **You:** Tags I create myself. Like "quick meals" or "batch cooking."
- **Claude:** What does a recipe look like? Title, ingredients, steps? Or simpler — just a title and some notes?
- **You:** Title, ingredients list, method steps, and maybe a prep time.

By the end of this conversation, Claude writes a brief — a short document that captures what you're actually building. The brief goes on `ROADMAP.md` as a planned feature. You haven't written a line of code, but you now have a clear target instead of a vague idea.

## What a session looks like

Claude creates a plan in `.claude/plans/recipe-book.md` with steps like:

1. Data model — define what a recipe looks like (title, ingredients, steps, tags, favourite flag)
2. Add recipe form — a page where you can type in a new recipe and save it
3. Recipe list with search — display all recipes, filter by typing in a search box
4. Favourites and tags — mark recipes as favourites, add/remove tags, filter by tag
5. Polish — layout, styling, empty states (what happens when there are no recipes yet?)

Each step gets added to `todo.md` with a contract — a set of testable criteria that define "done." Here's what the first two might look like:

```
## In Progress

1. [ ] Data model and storage
   Contract:
   - [ ] [auto] Recipe data structure defined. Verify: file: src/data/recipes.js exists
   - [ ] [auto] Can save and retrieve a recipe. Verify: run: node tests/storage.test.js

2. [ ] Add recipe form
   Contract:
   - [ ] [auto] Form page exists. Verify: html: index.html has .recipe-form
   - [ ] [auto] Submitting saves a recipe. Verify: run: node tests/add-recipe.test.js
   - [ ] [manual] Form is easy to fill in — fields are clear, nothing confusing
```

The `[auto]` items are things Claude can verify by running a command. The `[manual]` item is something that needs your eyes — does the form actually feel right to use?

### Session 1: Data model and form

The first session builds steps 1 and 2. Claude starts by defining the recipe data structure — what fields a recipe has, how it's stored. Then it builds the storage logic (save a recipe, load all recipes) and runs the contract checks.

The storage test fails on the first attempt: the "retrieve" function returns an empty array because it's reading from the wrong file path. Claude reads the error, spots the mismatch, fixes the path, and re-runs. The test passes. Step 1 gets committed to git with the message "Add recipe data model and storage."

Then Claude builds the add recipe form — input fields for title, ingredients, method, prep time, and tags. It runs the form contract checks: the form page exists (passes), submitting saves a recipe (passes). Step 2 gets its own commit.

At the end of the session, you run `/wrap`. Claude records what was built, what's next, and any decisions that were made (like "recipes are stored in localStorage for now — might move to a database later if the list gets large").

### Session 2: Search, favourites, polish

When you come back tomorrow and run `/stand-up`, Claude shows you exactly where you left off:

> Steps 1 and 2 are complete. Step 3 (search) is next. No blockers. Decision from last session: using localStorage for now.

You don't need to re-explain the project or remind Claude about your technology choices. It read STATE.md and already knows. Claude picks up step 3 and keeps building.

Search goes smoothly — Claude builds a text input that filters the recipe list as you type. The contract test checks that searching "chicken" actually returns only recipes with "chicken" in the title or ingredients, not every recipe in the list.

When Claude gets to step 4 (favourites), something feels off. You try the favourites toggle and it works, but you realise you also want to see a "Favourites only" filter at the top of the list — something that wasn't in the original plan. You tell Claude, it adjusts the step, updates the contract to include a test for the filter, and builds it. This is normal — plans evolve as you see the product take shape.

By the end of this session, the app works end to end. Claude presents the manual test checklist for the whole feature: check the form layout, try the search, toggle favourites, add and remove tags. You test, confirm everything looks right, and the feature is marked complete on `ROADMAP.md`.

## What DOE gives you

This walkthrough shows four DOE concepts working together:

**`/scope` turned a vague idea into a clear brief.** Without it, Claude would have started building immediately — probably guessing wrong about half the details. The scoping conversation cost five minutes and saved hours of rework.

**Contracts ensured the search actually works.** When Claude says "search is done," it means the test passed — not just that the code looks right. If the search was matching against recipe IDs instead of recipe names (a real mistake AI makes), the contract would catch it.

**Commits mean you can undo safely.** If you don't like how favourites turned out in step 4, you can undo that one step without affecting the search feature you built in step 3. Each step is its own save point.

**STATE.md means tomorrow's session picks up where today left off.** You don't need to re-explain the project, remind Claude about your decisions, or figure out what was done. The system remembers for you.

---

This is DOE at its simplest: take a loose idea, give it structure, build it in small verified steps, and never lose context between sessions. The recipe book is a small project, but the pattern scales to anything.
