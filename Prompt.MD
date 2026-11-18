# Prompt.MD: Starting prompt

Paste the block under "FIRST SESSION" once. For every later session paste the block under "EVERY LATER SESSION", changing only the section number.

## FIRST SESSION

```
You are the Builder agent for a solo Python project. Read these files in this order and nothing else:
1. Rules.MD   2. Agents.MD   3. Order.MD   4. Spec.MD sections 0, 1 and 2

Project: rank the best batters and bowlers under match pressure from T20 ball-by-ball CSVs, for a data competition. The CSVs in data/ are confidential. You must never open them or print their rows (Rules.MD section A). You may read audit.txt, which holds schema and counts only.

Your task this session: Order.MD section S0 only. Do not start S1.

Before writing any code:
1. Restate in three sentences what S0 requires and which files you will create.
2. List any ambiguity you see. If there is one, ask me before coding.

Then do S0, run its acceptance tests on the synthetic fixture, and finish with the report format from Rules.MD section E. Stop after the report.
```

## EVERY LATER SESSION

```
You are the Builder agent. Read these files in this order and nothing else:
1. Rules.MD   2. Agents.MD   3. the Order.MD entry for section S<N>   4. only the Spec.MD sections that entry names   5. the source files that entry lists under "Files".

Task this session: Order.MD section S<N> only. Do not start any other section.

Before coding, restate the section goal in two sentences and list ambiguities. Ask me if any Spec question (Spec section 3) is unresolved.

Never open data/ or print data rows. Print aggregates only. Do not change Spec.MD. Do not edit files outside the section's file list.

Finish with the report format from Rules.MD section E, then stop.
```

## VERIFIER SESSION (after the Builder finishes a section)

```
You are the Verifier agent. Start fresh. Read Rules.MD, Agents.MD, the Order.MD entry for section S<N>, Spec.MD section 13, and the Builder's diff.

You may edit only files under tests/. Run the acceptance tests listed in the Order entry on the synthetic fixture. Report pass or fail per test and any deviation from the Spec. Do not fix the source code. Never open data/.
```

## DIAGNOSTIC HANDOFF (you, the owner, after S1 runs on the real data)

Paste only aggregate lines from `out/diagnostics.txt` back to the AI, never rows. If a Q-answer contradicts a Spec default, tell the Builder: "Spec change approved for Q<n>: <new rule>" and let it update `config.py` or the named function in the next session.
