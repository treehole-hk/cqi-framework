# Conversation Quality Index (CQI)

A 7-dimension evaluation framework for assessing AI therapy conversation quality, with an explicit safety dimension (Dark Factor) for detecting clinically harmful patterns that users enjoy.

Developed by [TreeholeHK](https://treehole.hk) for evaluating [MindForest](https://mindforest.ai), a production AI mental health companion serving users in Hong Kong.

**Paper:** Chan, P. K. (2026). Evaluating MindForest's AI Therapy Readiness Using LLM-as-Judge: Therapeutic Containment Differentiates User-Approved from User-Rejected Responses. *Preprint.*

## Key Findings

- **Therapeutic Containment (TC)** is the strongest differentiator between user-liked and user-disliked AI responses (d = 0.76, p = .010)
- **User satisfaction is not a safety signal**: 28% of liked responses contained clinically concerning Dark Factor patterns
- TC alone outperforms any multi-dimension composite in predicting user satisfaction

## Repository Contents

```
cqi-framework/
  RUBRIC.md          # Full 7-dimension rubric with behavioral anchors
  data/
    cqi_scores.csv   # De-identified scores from 100 evaluation windows
  analyze.py         # Replication script reproducing all paper statistics
  requirements.txt   # Python dependencies
```

## Quick Start

```bash
pip install -r requirements.txt
python analyze.py
```

This reproduces all statistical tests from the paper (score distributions, psychometrics, criterion validity, incremental validity, Dark Factor analysis).

To use with your own CQI scores:

```bash
python analyze.py --data path/to/your_scores.csv
```

Your CSV needs columns: `sample_group` (liked/disliked/neutral), `CS`, `FD`, `CP`, `CN`, `TD`, `TC`, `DF`, `CQI`.

## The 7 Dimensions

| Dimension | Code | What it measures |
|-----------|------|-----------------|
| Clinical Skillfulness | CS | Right technique, right moment, right execution |
| Facilitative Depth | FD | User discovers own insights vs advice-giving |
| Contextual Precision | CP | Response fits this person in this conversation |
| Conversational Naturalness | CN | Avoids AI-specific pitfalls (sycophancy, formulaic patterns) |
| Therapeutic Direction | TD | Conversation moves forward productively |
| Therapeutic Containment | TC | Safe space for difficult material, holding without rescuing |
| Dark Factor | DF | Safety gate: detects popular-but-harmful patterns (6=clean, 1=harmful) |

See [RUBRIC.md](RUBRIC.md) for the full rubric with behavioral anchors at each score level.

## Data

`data/cqi_scores.csv` contains de-identified CQI scores for 100 message-level conversation windows (40 liked, 20 disliked, 40 neutral) from [MindForest](https://mindforest.ai), a production AI mental health companion app. All identifiers are hashed. No conversation text is included.

## Citation

If you use the CQI framework or data, please cite:

```bibtex
@article{chan2026cqi,
  title={Evaluating {MindForest's} {AI} Therapy Readiness Using {LLM}-as-Judge: Therapeutic Containment Differentiates User-Approved from User-Rejected Responses},
  author={Chan, Peter Kin-yan},
  year={2026}
}
```

## License

MIT (code and data). See [LICENSE](LICENSE).
