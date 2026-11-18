# Anti-money-laundering alerts, explained

A plain-English guide for readers who do not write code. Every number below comes from the **test period**, the last fifth of the data, which the model never saw while it was built. Full tables are in `results/ibm_compare.md`.

## 1. The problem: too many alerts

Banks watch every payment for signs of money laundering. The usual tool is a set of fixed rules, such as "many small payments just under a limit" or "money in and straight out again". Rules are easy to explain, but they are blunt.

On our test data the five rules raised **167,778 alerts**. Only **0.3%** of them were real laundering (that is *precision*), and together they caught only **28.3%** of the laundering that was there (that is *recall*). An analyst team cannot read 167,778 alerts, so most of them are never looked at properly. The real risk sits in the ones that are never read.

The question this project asks: can a ranking model put the likely cases first, so the same analysts find more with less work?

## 2. The data

We use the public IBM AML dataset, "HI-Small". It is synthetic: IBM simulated a bank world and planted laundering inside it, so the answers are known.

- **5.08 million** transactions, of which about **0.18%** are laundering. That is roughly one in 560.
- Laundering comes in **8 named patterns** (called typologies), such as one account paying many others, or money going round in a circle. A file lists which transactions belong to which pattern.
- Some laundering rows are not listed in that file. We call them "unlisted" and report them separately.

**The time split.** We sort the payments by time and use the first 60% to build the model, the next 20% to pick its settings, and the last 20% for the final exam. This matters because a real bank only ever knows the past. Shuffling the data would let the model peek at the future and flatter its score. The last 20% was never used to tune anything.

## 3. The pipeline in six steps

1. **Data.** Load the payments and the pattern file, and attach a pattern label to each laundering payment.
2. **Rules baseline.** Run the five rules. This is the "before" picture, and the model has to beat it.
3. **Ranking model.** A model called LightGBM gives every payment a score from 0 to 1. It looks at **16 facts about the payment, using only what was known before it happened**:
   - *Speed of activity* (6 facts): how many payments the sender made, and the receiver got, in the last hour, day and week. Sudden bursts are suspicious.
   - *Shape of the network* (3 facts): how many different accounts the sender has paid and the receiver has been paid by, and the ratio of money in to money out. Accounts that only pass money along stand out.
   - *Amount* (3 facts): the size, and whether it is a round number. Launderers like round figures.
   - *Bank and currency* (3 facts): whether the money crossed banks or changed currency, and which currency it was.
   - *How it was paid* (1 fact): the payment format, such as wire, cheque or card.
4. **Ranked alerts.** Sort by score. The analyst works from the top down, and the budget decides where to stop.
5. **Investigation.** For each top alert the system gathers the evidence (the sender's and receiver's last seven days, who they paid, how fast, how much), checks whether the pattern of payments looks like one of the named typologies, then writes a **case note** and a **draft suspicious transaction report (STR)**. Python does all the counting. The text only describes numbers that Python already produced, and a wording check blocks banned language. It says "refer for review", never a verdict.
6. **Analyst decision.** A person reads the case and decides. **Nothing is filed, frozen or sent automatically.** The analyst's decision is recorded on top of the system's answer and never overwrites it.

## 4. Results

| | Alerts | What it finds |
|---|---|---|
| Rules | 167,778 | 28.3% of laundering |
| Ranking model, same recall | **715** | 28.3% of laundering |
| Ranking model, rules' budget | 167,778 | **97.8%** of laundering |

- **Same recall, 235 times fewer alerts.** The model reaches the rules' 28.3% with 715 alerts instead of 167,778.
- **Same workload, far more caught.** Given the rules' whole budget, it finds 97.8% of the laundering.
- **At the top of the list it is sharp.** In the 100 highest-scored alerts, **95 were real** (precision@100 of 0.95).
- At the model's own cut-off it raises 1,655 alerts, with precision 53% and recall 49%.

## 5. Honesty checks

Good results deserve suspicion, so we tried to break them.

- **Leakage audit.** We listed every fact the model sees and confirmed it contains no account IDs, no pattern labels and nothing from the future. A test fails if that ever changes.
- **Payment-format ablation.** We retrained the model without the payment-format fact. Precision fell from **53% to 20%** and the top-100 score from 0.95 to 0.73. So a good part of the edge comes from *how* the money moved, not only from account behaviour. That is a real finding, not a footnote. It could reflect how IBM built the simulation.
- **A false alarm, shown on purpose.** Alert **IBM-4355742** scores 1.000 and sits near the top, yet the patterns file says it is not laundering. The pattern check found no named pattern, so the system fell back on a guess (gather-scatter), and the case note has no pattern-check line. This is what a high-scoring false alarm looks like, and the analyst is the safeguard.

## 6. Limits and next steps

- **Naming the pattern is weak.** The system names the typology correctly for about **40%** of test laundering rows. It is better at deciding *which payments to look at* than at saying *what scheme it is*.
- **Unlisted laundering is mostly missed.** Recall on those rows is 1.3%.
- **Linking payments into one case** is the next step. Today each alert is judged on its own, so a scheme spread across many payments is not yet seen as one case.
- In a follow-up experiment (github.com/coachuttam/aml-ibm-finetune, results/case_typology.md), classifying the whole group of linked payments instead of a single payment named the pattern correctly 76.8% of the time (95 attempts, time-only split). Most flagged alerts are single payments, which is why linking alerts into cases is the next step.
- **Synthetic data.** Real banks have messier data, real customers and shifting behaviour. These scores say nothing about live accuracy. Amounts are also in each row's own currency, with no exchange rates.
- **Next:** a sandbox pilot on a bank's own historical alerts, with its analysts, measuring how many cases they would have closed sooner and how often they overrule the system.

## 7. Glossary

- **AML (anti-money-laundering):** the rules and checks banks use to stop illicit money passing through them.
- **STR (suspicious transaction report):** the report a bank sends to the authorities when it suspects laundering. Here the system only drafts one; a person decides.
- **FIU-IND:** India's Financial Intelligence Unit, the body that receives STRs there.
- **Typology:** a named laundering pattern, such as fan-out or cycle.
- **Fan-out / fan-in:** one account paying many accounts, or many accounts paying one.
- **Cycle:** money that travels through several accounts and returns to where it started.
- **Precision:** of the alerts raised, the share that were real. Low precision means wasted analyst time.
- **Recall:** of all the real laundering, the share that was caught. Low recall means missed cases.
