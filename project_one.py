from openai import OpenAI, LengthFinishReasonError, APITimeoutError
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from typing import Literal, Optional
import json
from pathlib import Path

load_dotenv()
api_key = os.getenv("API_KEY")

job_list = sorted(Path("sample_jobs").glob("job_*"))


client = OpenAI(base_url="http://localhost:11434/v1", api_key=api_key, timeout=30, max_retries=0)
RESULTS = []

SYSTEM_PROMPT = (
    "Extract details from the job posting. "
    "remote is true only if the posting explicitly says fully remote; hybrid or unstated is false. "
    "salary_range is null if no salary is given. Do not guess."
)

class JobInfo(BaseModel):
    company: str
    title: str
    skills: list[str] = Field(max_length=10,
        description="Technical skills and tools only, such as programming languages, "
                    "software, or platforms. Exclude soft skills. Maximum 10.",)
    remote: bool = Field(default= False,
                         description="True only if the posting states it is fully remote. "
                                     "If nothing is stated, or it's hybrid, False.")
    seniority: Literal["intern", "entry", "mid", "senior", "lead", "unknown"]
    salary_range: Optional[str]= Field(default= None, description="The salary range of the job posting. None if nothing is given. ")



def get_page_contents(path):
    with open(path, "r", encoding="utf-8") as f:
          return f.read()

for i, job in enumerate(job_list, start=1):
    contents = get_page_contents(job)
    try:
        response = client.chat.completions.parse(
            model="llama3.2:1b",
            response_format=JobInfo,
            temperature=0,
            max_tokens=800,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Job Posting:\n\n{contents}"},
            ],
        )
    except LengthFinishReasonError as e:
        print(f"Job {i}: hit the token limit, skipped")
        print(e.completion.choices[0].message.content[:500])  # first 500 chars of what it wrote
        continue
    except APITimeoutError:
        print(f"Job {i}: timed out, skipped")
        continue
    parsed = response.choices[0].message.parsed
    if parsed is None:
        print(f" Job {i}: Failed to parse")
        continue
    RESULTS.append(parsed.model_dump())
    print(f"Job {i} done")

with open("Job_Description.txt", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=3)

