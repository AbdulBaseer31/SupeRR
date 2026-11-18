--- PAGE 1 ---
Pressure Players Spec: SupeRR Selector 
Round 1
Nov 16, 2026  ·  @Dan
Bottom line
Build a transparent statistics pipeline, not a model: a per-ball pressure index, a runs-
above-expected score per player, shrinkage for small samples, and a bootstrap that shows
how stable each rank is. No LLM, no fine-tuning, no GPU.
Cleaning: not a stage, but a validation pass is mandatory, and every delivery must end
up either used or listed in an exclusion ledger with a reason. That is the honest
reading of "every row accounted for".
Normalization: not column scaling. The normalization that matters is context:
baselines by competition, phase and wickets lost, so a T20I ball and an IPL ball are
compared to their own par.
The hard part is the argument, not the code. The code is a few hundred lines of
pandas. What wins or loses points is a defensible pressure definition and an honest
read of how much of "clutch" is real skill.
Two things I cannot know yet: what the CSVs actually contain (I have not seen them),
and how Round 1 is scored (the PDF does not say). Both are in the open questions at
the end.
Expect the final top 10 to overlap heavily with the best T20 players overall. If our pipeline
says otherwise, suspect the pipeline first.
What the problem asks, and what the PDF leaves open
The deliverable is fixed: a ranked top 10 of batters and a ranked top 10 of bowlers by
pressure performance, from IPL and T20I data since 2022, plus a methodology report. Five
things are left open or contradictory, and each one forces a decision.
Scoring is not stated. The ranking could be judged on report quality, on agreement
with Rajasthan Royals' own analysis, or both. We build for both: rankings we can
defend and a report someone else can reproduce. I have not heard of this specific
hackathon beyond what the PDF says, so check the Unstop page for the rubric,
deadline and team rules.
Pressure Players Spec: SupeRR Selector Round 1
Page 1 of 12
--- PAGE 2 ---
"Pressure" is ours to define, and the report must show that the definition separates
pressure from ordinary situations. That needs an explicit validation exhibit, not just an
assertion.
"Compared with their usual performance" versus "best-performing under
pressure" pull in different directions. A player who is elite in every situation has no
gap between pressure and usual. Section 7 resolves this.
The Unstop dropdowns limit who we can pick. Before locking rankings, confirm
every name in our top 20 appears in the dropdown, and that it maps to the same
player in the data.
Four seasons of data is thin. Per-player pressure samples will be hundreds of balls,
not thousands. That is why sections 8 and 9 (shrinkage, bootstrap) are not optional.
Scope
The scope is one reproducible script from raw CSVs to two ranked lists and the evidence
behind them. Anything that does not make the ranking more defensible is out.
In scope
Load every supplied file and reconcile row counts (the ledger in section 5).
Rebuild the match state at every legal delivery: innings, balls left, wickets lost, score,
and target and runs required in chases.
A pressure index per delivery, plus a simple rule-based version as a cross-check.
One scoring currency for batters and bowlers, with context par and each player's own
baseline.
Eligibility thresholds, shrinkage, match-level bootstrap, split-half consistency,
sensitivity to weights.
The 20 final names and the methodology report.
Out of scope
Neural networks, LLMs, gradient boosting or any model whose behaviour we cannot
explain in a sentence.
Dashboards or apps. The PDF asks for two lists and a document.
External data or reputation. The PDF says rankings must come from the supplied data.
The optional "share your journey" video. It does not affect evaluation, so it waits until
everything else is done.
Only if time remains
Pressure Players Spec: SupeRR Selector Round 1
Page 2 of 12
--- PAGE 3 ---
Opposition-strength adjustment for T20I matches.
Venue-specific par scores.
Fit with your build
Compute is a non-issue on your Ryzen 7 laptop. This is group-by arithmetic on a few
hundred thousand rows (my estimate; confirm with a row count), so the full pipeline
should run in seconds to a couple of minutes with no GPU. Set it as a rule: raw CSV to final
rankings in under five minutes, or something is wrong.
What I can and cannot judge about you:
Explaining things to non-experts is your visible strength. Your recent work is
teaching and training material, and the methodology report rewards exactly that:
clear definitions, reproducible steps, honest limits.
I have no evidence of your pipeline or fine-tuning experience. I am assuming
comfortable Python and pandas, no ML background, and no prior use of the statistics
below. Tell me if that is wrong and I will recalibrate.
The risk is statistics, not engineering. Shrinkage toward the league mean and a
match-level bootstrap are the two ideas you may not have used. Each is about 20 lines
of code, and I will explain each in the report's own words so you can defend it to a
judge.
Tooling: Python in a virtual environment on Fedora, pandas, numpy, matplotlib. Not
polars, not Spark, not a database. Familiar and sufficient beats fast and unfamiliar. One
script for the pipeline, one notebook for the report's charts.
Data: what you doubted, and what I disagree with
You are right that heavy cleaning and statistical normalization are probably unnecessary.
You are wrong if that extends to "no preparation": pressure is a property of match state,
and match state only exists if the deliveries are counted correctly. Those rules are cricket
semantics, not cleaning, and getting them wrong silently corrupts every rating.
The ledger. Every delivery row ends in exactly one bucket: used, or excluded with a
named reason. The counts must reconcile to the raw file to the row. This is how "each and
every row accounted for" is actually met. It does not mean every row influences the
ranking, and the report should say so plainly.
Pressure Players Spec: SupeRR Selector Round 1
Page 3 of 12
--- PAGE 4 ---
The supporting tables are used where they change a result: matches for outcomes and
abandoned games, playing XIs to know who actually played, mappings to join players
across competitions. Any table we audit and do not use gets one line in the report saying
so.
Item Verdict Why
Duplicate or missing keys
(match, innings, over, ball)
Check first Cheap to test, and a failure
invalidates everything
downstream.
Wides and no-balls Mandatory rule Not a legal ball for balls faced,
balls bowled or balls left.
Byes and leg-byes Mandatory rule Not charged to the bowler, and
not scored by the batter.
Dismissal credit Mandatory rule Run outs and retirements do
not count as bowler wickets.
Super overs, 3rd and 4th
innings
Decide and document Different structure. Likely
excluded from the index, with
the count reported.
Abandoned, no-result and rain-
revised matches
Exclude from target-
based states
A revised target breaks
required run rate. Use the
matches table to find them.
Shortened innings Mandatory rule Balls left must use that innings'
scheduled overs, not a fixed
120.
Player identity across IPL and
T20I
Check first One person may carry different
IDs or name spellings. Use the
players and mapping tables.
Nulls and odd values Only if found Exclude with a reason. Do not
impute.
Z-scores or min-max scaling of
columns
Not needed Nothing here feeds a distance-
based or gradient model.
Context baselines
(competition, phase, wickets)
Mandatory This is the normalization that
matters. See section 7.
Pressure Players Spec: SupeRR Selector Round 1
Page 4 of 12
--- PAGE 5 ---
First 30 minutes, before any design is final: row counts per file, key uniqueness, null
counts per column, competitions and seasons present, innings per match, ball counts per
innings, and ID overlap between IPL and T20I. Bring me those numbers and I will lock or
change the pressure design.
Pressure definition
Pressure is leverage: how far the next ball can move each side's chance of winning,
computed only from what was known at that ball. It folds required rate, wickets in hand,
balls left and closeness into one number, and it applies identically to the batter and the
bowler.
1. Win probability by lookup, not by model. Bucket the match state and take the
historical win rate of that bucket from the supplied data. Chases use balls left, wickets
lost and required run rate. First innings use balls bowled, wickets lost and score
against par for that point. Fit one table per competition. A bucket with too few
observations falls back to a coarser bucket.
2. Leverage per ball. Weight the swing in win probability for each possible outcome
(dot, 1, 2, 3, 4, 6, wicket) by how often that outcome occurs in that phase:
L_t = \sum_{o} P(o \mid \text{phase}) \, \left| WP(s_t \oplus o) - WP(s_t) 
\right|
3. Pressure flag. A ball is high-pressure if its leverage is in the top quartile within its
innings type. We set the cut by looking at the leverage distribution, not by fixing it
first. We also keep the continuous leverage as a weight for robustness checks.
4. Rule-based cross-check. A plain definition (chase with required rate well above
current rate, or wickets lost well above par for the over, or the final overs of a close
chase) run through the same pipeline. If the two definitions give very different top
10s, we report that instead of hiding it.
Be honest in the report about first innings. There is no target, so win probability there is
weak and leverage stays low and noisy. Pressure in this data is mostly a chase
phenomenon plus first-innings collapses and death overs. That is defensible, but it must
be stated.
The validation exhibit the PDF demands. Across all players, compare high-pressure and
ordinary balls within the same phase: dot-ball rate, boundary rate, dismissal rate, runs per
ball. If these do not differ, the definition is just "close game" with a label on it, and we
change it.
Pressure Players Spec: SupeRR Selector Round 1
Page 5 of 12
--- PAGE 6 ---
Leakage traps to avoid
No final result, margin or final score in any state. A game that ends by one run looks
tense from ball one if you let it.
No second-innings target when labelling first-innings balls.
Fit win-probability tables on one half of the matches and apply them to the other, so a
match is never used to judge itself. Alternate halves and average.
Performance currency and baselines
Both roles are scored in one currency: expected runs added per ball, measured against
par for the same situation. It handles scoring, dismissals and dots in a single number,
needs only a lookup table, and works the same for batting and bowling.
Build a table of expected remaining runs, ER, by balls left and wickets lost, per
competition and innings type. Then each delivery's value is:
V_t = r_t + ER(s_{t+1}) - ER(s_t)
Here r is the runs scored on the ball and s is the match state before and after it. A
boundary raises V, a dot lowers it, and a wicket lowers it by exactly what that wicket costs
in that phase. No hand-tuned wicket penalty is needed.
Three numbers per player.
P: mean value per ball on high-pressure balls.
Batters Bowlers
Value per ball V as above Minus V, using runs charged to the
bowler
Wickets Cost charged to the dismissed
batter
Credit only for bowler-credited
dismissals
Wides and no-
balls
Not a ball faced Runs charged, not counted as a legal
ball
Byes and leg-
byes
Not credited to the batter Not charged to the bowler
Unit Runs per 100 legal balls Runs saved per 100 legal balls
Pressure Players Spec: SupeRR Selector Round 1
Page 6 of 12
--- PAGE 7 ---
U: mean value per ball on ordinary balls, the player's own baseline.
Delta = P − U: the dip or lift under pressure.
The conflict from section 2, decided. Ranking on Delta alone rewards mediocre players
who happen to stay mediocre, and punishes stars with a high baseline. Ranking on P alone
ignores the PDF's "compared with usual levels". So:
1. Rank on shrunk P (section 8), because the submission asks for the best performers
under pressure.
2. Use Delta as a dip filter and a reported diagnostic. A player whose shrunk Delta is
clearly negative, meaning they are measurably worse under pressure than in ordinary
play, does not make the top 10 even with a high P. The cut is set after seeing the
distribution and stated in the report.
3. Show the alternatives. Report the top 10 under pure P, pure Delta and a 50/50 blend,
so the report shows how much the choice matters. Blend weights are a judgment call,
and that sensitivity table is the honest defence of it.
The par tables already absorb phase, wickets lost and competition, so an opener and a
finisher are each measured against their own situation. Batting position is not a separate
adjustment.
Fair comparison: samples, eligibility, IPL versus T20I
With four seasons of data, small samples are the main way this ranking goes wrong. A
player with 40 lucky pressure balls would otherwise top the list.
Eligibility floor. Minimum pressure balls faced or bowled, and a minimum number of
distinct matches with pressure exposure, because balls inside one match are not
independent. The numbers are placeholders until we see the distribution (I would
expect something around 100 pressure balls and 10 matches). We pick them from the
data, then publish a sensitivity table showing the top 10 at stricter and looser floors.
Shrinkage instead of a hard cutoff alone. Pull each player's P toward the league mean
in proportion to how little data they have:
P^{*} = \mu + \frac{n}{n + k}\,(P_{\text{obs}} - \mu), \qquad k = 
\sigma^{2}_{\text{noise}} \,/\, \sigma^{2}_{\text{true}}
Here n is the player's pressure balls, μ  the league mean, and k is estimated from the data
by the method of moments, so we do not pick it by hand. This is the single most defensible
step in the report.
Pressure Players Spec: SupeRR Selector Round 1
Page 7 of 12
--- PAGE 8 ---
IPL and T20I together. Each ball is scored against its own competition's par, so values
are comparable in a first-order sense, and a player's P pools both, weighted by balls.
We also publish IPL-only and T20I-only top 10s as a robustness check.
The weak spot: opposition quality. If the T20I data includes associate nations, a
batter facing them is not comparable to one facing full members, and par does not fix
that. Check which teams appear in the competition-team mappings. Either restrict
T20I to a defined set of teams or add an opposition-strength weight, and say which in
the report.
Bowlers need their own floor. Count legal balls bowled under pressure, so part-time
bowlers with a handful of overs do not qualify by accident.
Match context beyond state. Venue and pitch are not adjusted unless time allows.
The report lists this as a limitation rather than pretending it is handled.
Ranking and reliability checks
The final order is the order of shrunk P among eligible players who pass the dip filter,
taken separately for batters and bowlers. Every check below exists to tell the reader how
much to trust that order, and none of them is allowed to reshuffle it after the fact.
Match-level bootstrap. Pre-aggregate to one row per player per match (pressure
balls, pressure value, ordinary balls, ordinary value). Resample matches with
replacement about 1,000 times and recompute P* each time. Report each finalist's
rank interval and the share of resamples in which they land in the top 10. Resampling
matches, not balls, respects the clustering. It is cheap because it works on the small
aggregated table.
Split-half reliability. Split matches into two halves (alternating, or by season) and
correlate P* between halves across eligible players. This answers whether pressure
performance is a stable trait. Research on clutch performance in other sports
generally finds weak persistence, and I expect something similar here, but the
number has to come from this data. A low value is not a failure. Reporting it honestly is
a strength.
Consistency across matches. For each finalist: share of pressure innings or spells
with positive total value, median per-match value, and P by season.
Sensitivity grid. Re-run with pressure cut at top 20%, 25% and 33%, with the rule-
based definition, with stricter and looser floors, and with IPL-only and T20I-only data.
A finalist who stays in the top 10 in most variants is robust, and the report says which
finalists are not.
Pressure Players Spec: SupeRR Selector Round 1
Page 8 of 12
--- PAGE 9 ---
Names as a bug detector only. If a result looks absurd, we hunt for a data or identity
error. We do not tune the method until familiar names appear. The PDF says rankings
must come from the data, not reputation, and a judge can tell.
AI and LLM verdict
You are not wrong: nothing in this build needs an LLM or fine-tuning, and a model would
make the submission worse, not better.
No labels, no accuracy. There is no ground-truth list of "the most reliable players
under pressure" to train against or score against. So "accuracy" here can only mean
two things: the accounting is correct (the ledger reconciles, the cricket rules are
applied right) and the ranking is stable (bootstrap, split-half, sensitivity). A model with
a train-test score would be measuring nothing.
The "tuning" is threshold choice, not training: the pressure cut, the eligibility floors,
the shrinkage constant. We set these by inspecting distributions and then show a
sensitivity table, never by optimizing toward a result we like.
Where ML is tempting and wrong. A gradient-boosted win-probability model would
be slightly smoother than the lookup table. It would also be harder to explain, easier to
leak, and unnecessary for a leverage score. Logistic regression on state features is a
legitimate classical fallback if the lookup buckets turn out too sparse, but it is not
planned.
Where an LLM is fine: drafting and editing the report text and helping write the code,
as I am doing now. It stays out of the scoring path entirely, because the PDF asks for a
method someone else can reproduce.
Pipeline and compute
The pipeline is eight stages in a straight line, each with an output file and one check it
must pass before the next stage runs. Every stage is vectorized pandas and should finish
in well under a minute.
# Stage Output Check it must pass
1 Load files, build the ledger ledger.csv Used plus excluded rows equal
the raw row count, per file
Pressure Players Spec: SupeRR Selector Round 1
Page 9 of 12
--- PAGE 10 ---
Reproducibility. One requirements file with pinned versions, a README stating the run
order, a fixed random seed for the bootstrap, and a printed hash of each input file so a
reader can confirm they are running on the same data. Intermediate files are plain CSV so
any stage can be inspected in a spreadsheet.
Compute budget. Target under five minutes end to end on your laptop. If one stage takes
minutes, that is a vectorization bug or a loop over rows, and I would rather fix it than wait
for it.
Methodology report outline
The report mirrors the five things the PDF says it must cover, in the same order, so a judge
can tick them off. Aim for 6 to 10 pages, with tables and charts carrying the argument and
prose kept short.
# Stage Output Check it must pass
2 Rebuild match state per legal
ball
state table Balls per innings match the
scheduled overs, wickets
never exceed 10
3 Fit win-probability and
expected-runs tables
(alternating halves)
par tables No bucket falls below the
minimum observations without
a fallback
4 Leverage and pressure flag flagged balls Pressure and ordinary balls
differ within phase (the
validation exhibit)
5 Value per ball, batting and
bowling
value table Per match, batting and bowling
totals are opposites except
byes, leg-byes and non-bowler
dismissals
6 Aggregate to player per
match
aggregate table Totals equal the stage 5 sums
7 Shrink, filter, rank rankings.csv Every ranked name exists in
the Unstop dropdown
8 Bootstrap, split-half,
sensitivity
report tables and
charts
Fixed seed reproduces the
same numbers
Pressure Players Spec: SupeRR Selector Round 1
Page 10 of 12
--- PAGE 11 ---
The limitations section should name at least these: weak first-innings win probability, no
venue or pitch adjustment, four seasons of data, opposition quality in T20I, and low
expected persistence of pressure performance.
Risks, open questions and next steps
The likeliest way to lose is a ranking that looks like a list of famous names with no
pressure-specific story. The pressure definition being judged arbitrary is the second.
Where we can lose points
No pressure-specific story. Mitigation: for each finalist show their rank on overall
value next to their rank under pressure, and their Delta. The movement between
those two is the evidence that we measured pressure and not just quality.
Definition judged arbitrary. Mitigation: the validation exhibit and the rule-based
cross-check.
PDF requirement Report section Exhibits that prove it
Pressure definition 1. Defining pressure Leverage formula, win-probability
table, pressure versus ordinary
comparison chart, rule-based cross-
check
Performance
measurement
2. Scoring batters and
bowlers
Value-per-ball definition, par tables,
P, U and Delta, one fully worked
example delivery
Fair comparisons 3. Samples, eligibility, IPL
and T20I
The ledger table, eligibility floors,
shrinkage, how T20I opposition is
handled
Evidence for your top 10 4. Results Two ranking tables (P*, pressure
balls, Delta, rank interval) and a rank-
interval chart per list
Reliability and
limitations
5. How far to trust this Split-half correlation, bootstrap top-
10 probabilities, sensitivity grid, plain
list of limitations
Reproducible by
someone else
Appendix Run order, pinned versions, seed,
input file hashes
Pressure Players Spec: SupeRR Selector Round 1
Page 11 of 12
--- PAGE 12 ---
Small samples crowning a fluke. Mitigation: shrinkage, floors, bootstrap.
Identity or ID errors across IPL and T20I. Mitigation: the first-30-minutes audit.
Overbuilding. If time is short, cut in this order: opposition adjustment, then most of
the sensitivity grid. Never cut the ledger, the shrinkage or the bootstrap.
Open questions for you
What is the deadline, and is it a solo or team entry? This sets how much of the optional
work survives.
What does the Unstop page say about judging criteria?
What are the CSV file names, column names and row counts? I will lock the state-
rebuild logic from these.
Is my assumption about your background right: comfortable with Python and pandas,
no prior use of shrinkage or bootstrap?
Next steps
Check the Unstop page for rubric, deadline and the dropdown player list
Run the 30-minute audit from section 5 and send me the numbers
Send me the column headers of each file so I can write stages 1 and 2 (ledger and
match state)
Review the pressure definition in section 6 after seeing the leverage distribution, and
lock the cut
Draft the report sections alongside the code, not after it
Pressure Players Spec: SupeRR Selector Round 1
Page 12 of 12