# IBM AML: rules versus LightGBM

Data: IBM HI-Small (5078345 transactions, 5177 laundering, base rate 0.1769% in the test period). Temporal split 60/20/20 by time; the threshold is chosen on validation, and every number below is the **test** period.

## Overall (test period)

| System | Alerts | Precision | Recall | Minority F1 | PR-AUC | Precision@100 |
|---|---|---|---|---|---|---|
| Rules (any of R1-R5) | 167778 | 0.0030 | 0.283 | 0.006 | n/a | n/a (no ranking) |
| LightGBM | 1655 | 0.5317 | 0.490 | 0.510 | 0.460 | 0.95 |
| Hybrid (model OR R3) | 18383 | 0.0521 | 0.533 | 0.095 | n/a | n/a |

## Each rule alone (test period)

| Rule | Alerts | Precision | Recall |
|---|---|---|---|
| R1 | 2550 | 0.0035 | 0.005 |
| R2 | 130875 | 0.0015 | 0.112 |
| R3 | 16823 | 0.0065 | 0.061 |
| R4 | 12240 | 0.0114 | 0.078 |
| R5 | 10161 | 0.0067 | 0.038 |
| any_rule | 167778 | 0.0030 | 0.283 |

## Recall by typology (test period)

| Typology | Rules | LightGBM | Hybrid |
|---|---|---|---|
| BIPARTITE | 0.108 | 0.486 | 0.486 |
| CYCLE | 0.284 | 0.459 | 0.459 |
| FAN_IN | 0.139 | 0.715 | 0.723 |
| FAN_OUT | 0.293 | 0.721 | 0.721 |
| GATHER_SCATTER | 0.222 | 0.773 | 0.778 |
| RANDOM | 0.209 | 0.570 | 0.570 |
| SCATTER_GATHER | 0.333 | 0.631 | 0.683 |
| STACK | 0.171 | 0.507 | 0.507 |
| UNLISTED | 0.426 | 0.013 | 0.148 |

The hybrid adds R3, the rule with the best F1 on UNLISTED transactions in the training period (never chosen on test).

## Class weight (chosen on validation PR-AUC, never on test)

| Weight on the laundering class | Validation PR-AUC |
|---|---|
| 1.0 | 0.3116 |
| 10.0 | 0.0249 |
| balanced | 0.0144 |

Chosen: 1.0.

Most-used model features (split counts): receiver_in_degree (132), log_amount_paid (126), sender_in_out_ratio (123), payment_format_code (114), sender_sent_1h (108), receiver_received_1h (106), sender_out_degree (94), sender_sent_7d (91).

## Notes

- Rule thresholds were set by looking at the first 60% of the timeline only.
- Amounts are in each row's own currency; there are no exchange rates, so amount features are rough.
- Features use only past transactions. Account degree and in/out ratio are running totals,
  not whole-dataset values.
- Rules only say yes or no, so PR-AUC and precision@100 do not apply to them.
