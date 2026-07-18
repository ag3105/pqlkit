# pqlkit

Format and explain **PQL**, the Profile Query Language behind every audience in Adobe Real-Time CDP.

Every segment you build in the Adobe Experience Platform UI compiles down to PQL. When an audience returns 12 people instead of 12,000, the PQL is where the answer lives. The problem is that it usually arrives as one long unbroken line.

`pqlkit` does two things:

1. **Formats** it, so you can actually read the structure.
2. **Explains** it in plain English, so you can hand it to a stakeholder who does not write queries.

No Adobe credentials required. It works on the query text itself.

## Install

```bash
pip install pqlkit
```

Or from source:

```bash
git clone https://github.com/ag3105/pqlkit.git && cd pqlkit
pip install -e .
```

## Use it from the command line

```bash
pqlkit 'homeAddress.countryISO = "CA" and person.birthYear = 1985'
```

```
homeAddress.countryISO = "CA" and
person.birthYear = 1985
```

Add `--explain` for the plain-English version:

```bash
pqlkit --explain 'homeAddress.countryISO = "CA" and person.birthYear = 1985'
```

```
Includes people based on profile attributes.
  - home country is CA
  - birth year is 1985
  - All of the above conditions must be true.
```

It also reads from stdin, which is handy when you have pulled a segment definition from the API:

```bash
cat segment.pql | pqlkit --explain
```

## Use it from Python

```python
from pqlkit import format_pql, explain

query = (
    'let S = (sum X.commerce.order.priceTotal over X from xEvent '
    'where X.commerce.order.currencyCode = "USD") in (S > 100 and S < 1000)'
)

print(format_pql(query))
print(explain(query))
```

```
let S = (
  sum X.commerce.order.priceTotal over X from xEvent where X.commerce.order.currencyCode = "USD"
)
in (
  S > 100 and
  S < 1000
)

Includes people based on a calculated total across their events.
  - currency code is USD
  - All of the above conditions must be true.
  - Aggregates events using sum, so the whole event history is scanned. Watch the cost on high-volume profiles.
```

## What the explainer catches

- Whether a segment reads **profile attributes**, **event history**, or an **aggregate** across events.
- `exists` (at least one matching event) versus `forall` (every event must match).
- Each comparison, with XDM paths translated into readable phrases (`homeAddress.countryISO` becomes "home country").
- **Mixed AND/OR**, which is the most common cause of an audience coming back a surprising size. The explainer flags it so you go and check the parentheses.
- Aggregations that scan a full event history, which is where segment cost tends to hide.

## Scope and honest limitations

PQL has no published formal grammar. `pqlkit` uses a pragmatic tokenizer built around the constructs in Adobe's documented examples, not a complete parser. That means:

- It will format and explain the queries you meet in practice.
- It does **not** validate your PQL. A query that formats cleanly can still be wrong.
- Exotic or deeply nested expressions may format more conservatively than you would by hand.
- The explainer is a reading aid, not a specification. When precision matters, read the query.

Bug reports with a real query that formats badly are the most useful thing you can contribute.

## Contributing

Issues and pull requests welcome. If you hit a query that formats or explains poorly, open an issue with the query and what you expected. Run the tests with:

```bash
python -m pytest
```

## License

MIT
