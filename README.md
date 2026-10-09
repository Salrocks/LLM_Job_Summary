# Job Posting Extractor

A Python script that reads job postings from text files and uses a local LLM (via Ollama) to pull out structured details: company, title, skills, remote status, seniority, and salary range. Results are validated with Pydantic and saved as JSON.

Built as a week 1 project on my AI engineering learning path.

## How it works

1. Finds every posting file in `sample_jobs/` with `pathlib`
2. Sends each posting to a local model through Ollama's OpenAI-compatible API
3. Uses a Pydantic schema as the `response_format`, so the model must return JSON matching that shape
4. Skips any job that hits the token limit or times out, so one bad posting doesn't stop the run
5. Writes all successful results to a JSON file

## Tech stack

- Python 3
- [Ollama](https://ollama.com) running `llama3.2:1b` / `llama3.2:3b` locally
- `openai` SDK (pointed at the local Ollama server)
- `pydantic` for the output schema and validation
- `python-dotenv` for environment variables

## Setup

```bash
# install and start Ollama, then pull a model
ollama pull llama3.2:1b
ollama pull llama3.2:3b

# create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ollama doesn't check the API key, so any value works in `.env`:

```
API_KEY=ollama
```

## Usage

Put each job posting in its own file in `sample_jobs/` (named `job_1`, `job_2`, ...), then run:

```bash
python project_one.py
```

## Output schema

| Field | Type | Notes |
|---|---|---|
| `company` | `str` | Hiring company |
| `title` | `str` | Job title |
| `skills` | `list[str]` | Technical skills only, max 10 |
| `remote` | `bool` | `true` only if the posting says fully remote |
| `seniority` | `intern` / `entry` / `mid` / `senior` / `lead` / `unknown` | |
| `salary_range` | `str` or `null` | `null` if no salary is listed |

## What I learned

- **Structured output with Pydantic.** Passing a Pydantic model as `response_format` makes the model return JSON in a fixed shape, and `Literal` restricts fields to a set of allowed values.
- **Descriptions are guidance, constraints are rules.** A field's `description` is sent to the model as an instruction but isn't enforced. Constraints like `max_length` and `Literal` are.
- **Debugging a repetition loop.** One posting made the 1B model repeat items in the `skills` list until it ran out of tokens. Adding `max_tokens`, a timeout, and `max_length=10` on `skills` fixed it.
- **Small mistakes in constraints matter.** Writing `min_length=10` instead of `max_length=10` forced the model to invent skills and broke every job.
- **Penalties can break JSON.** `frequency_penalty` punishes repeated tokens, but JSON relies on repeated quotes, commas, and brackets, so it made every run fail.
- **Error handling for LLM calls.** `max_retries=0` makes timeouts fail fast, and catching `LengthFinishReasonError` and `APITimeoutError` lets the script skip a bad job and keep going.

## Known limitations

With `llama3.2:1b`, the output had some recurring mistakes:

- Sometimes put the location in the `company` field
- Marked a job as remote when the posting never mentioned it
- Included soft skills (communication, teamwork) despite the instructions
- Duplicated skills or combined several into one string

## Possible next steps

- Clean the skills list in code (split combined entries, remove duplicates)
- Save results to CSV for viewing in a spreadsheet
- Compare a score for each job against my own skill set
