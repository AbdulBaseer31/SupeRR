# Agents.MD: Subagent rules for Gemini 3.8 Flash (medium) in Antigravity
All agents obey `Rules.MD`. Where this file is stricter, this file wins.

## 1. Roles (maximum three; run one at a time)

### Builder
- Writes the code for exactly one section from `Order.MD`.
- May edit only the files listed in that section.
- Reads only the Spec sections named in that section.
- Ends with the report in `Rules.MD` section E.

### Verifier
- Starts from a clean context. Reads the Builder's diff, the section's acceptance tests in `Order.MD`, and `Spec.MD` section 13.
- May create or edit only files under `tests/`. It never edits `src/` or `pressure/`.
- Runs the tests on the synthetic fixture, prints pass or fail per test, and lists any deviation from the Spec.
- Does not fix the code. It returns findings to the Builder via the owner.

### Scribe (optional, only at the end of a section)
- Adds docstrings and one line to `CHANGELOG.md`.
- Makes no logic changes. Its diff must contain only comments, docstrings and the changelog line.

## 2. Parallelism

- Never run two agents that can edit the same file. Default: strictly sequential: Builder, then Verifier, then Scribe.
- Do not spawn extra subagents on your own. The owner starts each role.
- Never let any agent run more than one `Order.MD` section.

## 3. Context hygiene (important for a small-context model)

1. Each agent receives: `Rules.MD`, this file, its section of `Order.MD`, and the Spec sections that section names. Nothing more.
2. Do not paste whole files into the conversation. Refer to files by path and read line ranges.
3. After 20 or more tool calls in one session, stop, write the Rules.MD section E report, and let the owner start a fresh session.
4. Never keep large DataFrames printed in the chat. Print shapes and summaries.
5. Long outputs go to `out/` or `run_log.txt`, not into the chat.

## 4. Handoff note (Builder to Verifier, written by the Builder)

```
SECTION: S<n>
FILES CHANGED: ...
HOW TO RUN: <one command>
WHAT I ASSUMED: <list, or none>
KNOWN GAPS: <list, or none>
```

## 5. Escalation to the owner

Use this wording when blocked:

```
BLOCKED: <one sentence>
WHAT I TRIED: <one or two sentences>
WHAT I NEED FROM YOU: <a specific decision or a specific aggregate printout>
```

Do not proceed on a guess when the blocker is a Spec question (section 3 Q-questions) or a data-semantics question.

## 6. Failure modes to watch for (weaker models)

- Over-editing: rewriting a file to change three lines. Use targeted edits.
- Inventing column meanings. Run the diagnostics instead.
- Silently changing a formula "for stability". Do not. Report it as a proposed Spec change.
- Adding libraries or frameworks. Do not.
- Printing data rows while debugging. Forbidden by `Rules.MD` A.
- Declaring done without running the tests. A section is not done until the tests have run.
