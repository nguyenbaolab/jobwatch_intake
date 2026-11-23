# Rules for gold labels on job postings

Purpose: each posting in the set of 100 has one label file that you fill in by hand. Later, an extractor's output is compared field by field with this label. A wrong label makes the score wrong, so the rules stay fixed before the first posting is labeled. If a rule changes partway through, label the finished postings again.

## How to do it

1. Save the posting with `python -m jobwatch_intake <draft file> --out data/jobs` so you get `data/jobs/<job_id>.json`.
2. Copy that `job_id` into the label file `data/labels/<job_id>.json`. Two example postings have labels in `examples/labels/`.
3. Label **before** you look at a model's extraction. If you look first, you will label toward the model without noticing.
4. When the posting is ambiguous, follow the rule below and write the reason in `notes`. One line is enough.

The posting and the label live in different directories so an extractor can read the posting and cannot read the answer.

## Eight rules

1. **Label only what the text says.** Do not infer from the company name, the industry, or personal experience. If the text does not mention it, leave the default (`not_mentioned`, `unspecified`, `null`, or an empty list).

2. **Language (finnish, swedish, english) is the most important field.** Each language has two parts:
   - `requirement`: `required` when the posting says it is needed, mandatory, "vaaditaan", "required", "must", or lists it under requirements with no softening word. `preferred` when the posting says it is an advantage, "eduksi", "a plus", "nice to have", or "useful". `not_mentioned` when it is not mentioned.
   - `level`: `unspecified` when the posting only says "language X is needed" and gives no level. The other levels: `basic` (alkeet, basic), `good` (hyvä, good, enough to do the work, "työskentelyyn riittää"), `fluent` (sujuva, erinomainen, fluent, excellent), `native` (äidinkieli, native). Once the requirement is `not_mentioned`, `level` must be `unspecified`.

3. **Write a skill in lowercase, one concept per item.** `python`, `sql`, `docker`, `azure`. Do not write "Python-osaaminen"; write `python`. Do not write an item that is too broad, such as "cloud services" or "teamwork"; if it is worth remembering, put it in `notes`.

4. **required or preferred for a skill.** A tool the posting says you will use every day is `required`, even when it sits outside the requirements list. A tool with "plus", "eduksi", or "nice to have" is `preferred`. One skill is not in both lists.

5. **"A tai B" (A or B).** Put both A and B in `skills_required` and say in `notes` that they are alternatives. This keeps the rule simple and gives up a little precision.

6. **Years of experience are the minimum.** "vähintään 2 vuotta" or "at least 2 years" is `2`. "2-4 years" is `2`. "Kokemusta" with no number is `null`. Do not turn months into rounded years: "6 kuukautta" is `0`, and say so in `notes`.

7. **City and work mode.** `city` is the city where the work happens, in English when an English name exists (Helsinki, Tampere, Turku). Several cities: take the first city and put the others in `notes`. `work_mode` is `onsite`, `hybrid`, or `remote`. "pääosin toimistolla" (mostly at the office) is `onsite`. If the posting says nothing, use `unspecified`.

8. **The deadline is ISO `YYYY-MM-DD`.** A Finnish date `10.12.2026` is day.month.year, so `2026-12-10`. A US date `12/10/2026` depends on context; write `notes` if you are not sure. "jatkuva haku" (open application) or no deadline is `null`.

## Examples with an explanation

The two files `examples/labels/*.json` are sample labels for the two fictional postings in `examples/`. Read their `notes` to see how a reason is written.

## Checking a label

`GoldLabelFileDTO` rejects a label with the wrong shape (a missing required field, a wrong type, a bad date, an unknown field, or a misspelled name inside a language block). `GoldLabel` rejects a label that breaks a business rule (an empty skill, a repeated skill, a skill in both lists, `not_mentioned` with a `level`, or years outside 0..30). This command runs both:

```powershell
python -c "import json,sys; from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO; print(GoldLabelFileDTO.model_validate(json.load(open(sys.argv[1], encoding='utf-8'))).to_domain().job_id)" data/labels/job-xxxx.json
```

Generate the schema so VS Code reports errors while you type: `python tools/make_schemas.py`, then add this at the top of the label file:

```json
"$schema": "../../schemas/gold_label.schema.json"
```

The schema describes the file shape. Business rules live in the domain, not in the schema.
