import os
import re
import pandas as pd
import requests
import time
from dotenv import load_dotenv

# --- Part 1: SETUP ---

load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")

if not API_KEY:
    print("Error: RAPIDAPI_KEY not found in .env file.")
    exit()

# --- CONFIGURATION ---
TARGET_JOB_TITLES = [
    "Data Scientist", "Data Analyst", "AI Engineer", "Machine Learning Engineer",
    "ML Engineer", "AI/ML Engineer", "NLP Engineer", "GenAI Engineer",
    "Computer Vision Engineer", "Research Engineer AI/ML", "AI Solutions Engineer",
    "Applied Scientist AI/ML", "AI Research Scientist", "Junior Data Engineer",
    "Cloud Data Engineer", "Big Data Engineer", "Backend Developer Python SQL",
    "MLOps Engineer"
]

EXCEL_OUTPUT_FILE = "Output/found_jobs.xlsx"

# Filter behavior:
# True  = keep ONLY jobs that explicitly mention sponsorship (OPT/CPT/H-1B/etc.)
# False = keep jobs that do NOT prohibit sponsorship, even if they don't explicitly say they sponsor
STRICT_REQUIRE_SPONSOR_MENTION = True

# Add "visa sponsorship" hint to the search to bias API results toward sponsorship-friendly roles
ADD_SPONSORSHIP_HINT_TO_QUERY = True

# --- Part 2: FILTERS ---

# Phrases that usually mean NO sponsorship or US citizenship/GC required
BLOCK_PATTERNS = [
    r'\bus\s*citizen\b', r'\bu\.s\.\s*citizen\b', r'\bcitizenship\s*required\b',
    r'\bmust\s+be\s+(a\s+)?(us|u\.s\.)\s*citizen\b',
    r'\bgreen\s*card\b', r'\bgc\s*holder\b', r'\bpermanent\s*resident\b',
    r'\bus\s*person(s)?\b',
    r'\b(public\s*trust|secret|ts\/?sci|clearance).*(citizen|us\s*person)\b',
    r'\bno\s*visa\s*sponsorship\b',
    r'\b(not|unable|cannot|can\'t)\s+(provide|offer)\s+visa\s*sponsorship\b',
    r'\b(no|without)\s+(work\s*)?sponsorship\b',
    r'\bmust\s+be\s+authorized\s+to\s+work\s+in\s+the\s+us\s+without\s+sponsorship\b',
    r'\b(need|requires?)\s+(indefinite|permanent)\s+work\s+authorization\b',
]

# Phrases that indicate sponsorship is possible/likely
ALLOW_PATTERNS = [
    r'\bvisa\s*sponsorship\b', r'\bsponsor(s|ship)?\b', r'\bsponsoring\b',
    r'\bh-?1b\b', r'\bh1b\b', r'\bh1\-b\b',
    r'\bopt\b', r'\bstem\s*opt\b', r'\bcpt\b',
    r'\bf-?1\b', r'\bf1\b',
    r'\btn\s*visa\b', r'\be-?3\b', r'\bo-?1\b'
]

BLOCK_RES = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]
ALLOW_RES = [re.compile(p, re.IGNORECASE) for p in ALLOW_PATTERNS]

def _flatten(value):
    """Safely flatten strings/lists/dicts to a single text blob for regex search."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k}: {_flatten(v)}" for k, v in value.items())
    return str(value)

def sponsorship_filter(job):
    """
    Returns (keep: bool, note: str).
    keep == True only if it doesn't hit blocklist and (if STRICT) it hits allowlist.
    """
    text_fields = [
        job.get('job_title', ''),
        job.get('job_description', ''),
        job.get('job_employment_type', ''),
        job.get('job_required_skills', ''),
        job.get('job_highlights', ''),  # often dict with sections
        job.get('job_benefits', ''),
        job.get('employer_name', '')
    ]
    blob = _flatten(text_fields)

    # Blockers first
    for rx in BLOCK_RES:
        if rx.search(blob):
            return (False, "Blocked: citizenship/GC/no sponsorship requirement found")

    # If strict, require an explicit positive signal
    if STRICT_REQUIRE_SPONSOR_MENTION:
        for rx in ALLOW_RES:
            m = rx.search(blob)
            if m:
                return (True, f"Allows: explicit sponsorship signal ('{m.group(0)}')")
        return (False, "Skipped: no explicit sponsorship mention")
    else:
        # Permissive mode: passes as long as no blocker
        # Prefer to tag if we spotted a positive signal anyway
        for rx in ALLOW_RES:
            m = rx.search(blob)
            if m:
                return (True, f"Allows: explicit sponsorship signal ('{m.group(0)}')")
        return (True, "Allows: no blocker found (no explicit mention)")

# --- Part 3: HELPER FUNCTIONS (I/O) ---

def load_existing_job_ids(file_path):
    """Loads job IDs from an existing Excel file to prevent duplicates."""
    if not os.path.exists(file_path):
        return set()
    try:
        df = pd.read_excel(file_path)
        return set(df['Job ID'].astype(str).tolist())
    except (FileNotFoundError, KeyError, ValueError):
        return set()

def save_jobs_to_excel(jobs_list, file_path):
    """Creates or appends a list of jobs to an Excel file."""
    if not jobs_list:
        return
    
    # Map fields, plus Sponsorship Note
    columns = {
        'job_id': 'Job ID',
        'job_title': 'Title',
        'employer_name': 'Company',
        'job_city': 'City',
        'job_state': 'State',
        'job_apply_link': 'Application Link',
        '_sponsorship_note': 'Sponsorship Note'
    }

    # Build a clean list of rows with only known keys
    projected = []
    for j in jobs_list:
        row = {k: j.get(k, "") for k in columns.keys() if k != '_sponsorship_note'}
        row['_sponsorship_note'] = j.get('_sponsorship_note', '')
        projected.append(row)

    new_jobs_df = pd.DataFrame(projected)[list(columns.keys())].rename(columns=columns)

    if os.path.exists(file_path):
        with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            existing_df = pd.read_excel(file_path)
            new_jobs_df.to_excel(writer, startrow=len(existing_df) + 1, header=False, index=False)
    else:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        new_jobs_df.to_excel(file_path, index=False)

# --- API ---

def find_jobs(query):
    """Searches for jobs using the JSearch API."""
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}

    q = f"entry level to mid level {query} in USA"
    if ADD_SPONSORSHIP_HINT_TO_QUERY:
        q += " with visa sponsorship"

    params = {"query": q, "num_pages": "1"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException:
        return []

# --- Part 5: MAIN EXECUTION ---
if __name__ == "__main__":
    existing_job_ids = load_existing_job_ids(EXCEL_OUTPUT_FILE)
    print(f"Found {len(existing_job_ids)} jobs already in '{EXCEL_OUTPUT_FILE}'.")

    new_jobs_to_save = []
    kept_count = 0
    skipped_blocked = 0
    skipped_no_explicit = 0

    print("\n--- Starting Targeted Job Search (International-friendly) ---")

    for job_title in TARGET_JOB_TITLES:
        print(f"Searching for: '{job_title}'...")
        jobs_from_api = find_jobs(job_title)

        for job in jobs_from_api:
            job_id = str(job.get('job_id', '') or '').strip()
            if not job_id:
                continue
            if job_id in existing_job_ids:
                continue

            keep, note = sponsorship_filter(job)
            if keep:
                job['_sponsorship_note'] = note
                new_jobs_to_save.append(job)
                existing_job_ids.add(job_id)
                kept_count += 1
            else:
                if "Blocked:" in note:
                    skipped_blocked += 1
                else:
                    skipped_no_explicit += 1

        time.sleep(1)  # be polite to the API :)

    # --- Save and report ---
    if new_jobs_to_save:
        print(f"\n--- Found {len(new_jobs_to_save)} new sponsorship-friendly job openings! ---")
        save_jobs_to_excel(new_jobs_to_save, EXCEL_OUTPUT_FILE)
        print(f"All new jobs have been saved to '{EXCEL_OUTPUT_FILE}'")

        # Show a few samples
        for i, job in enumerate(new_jobs_to_save[:10], 1):
            print(f"  -> {i}. {job.get('job_title')} at {job.get('employer_name')} [{job.get('_sponsorship_note')}]")
    else:
        print("\n--- No new sponsorship-friendly openings found based on the current filters. ---")

    print(f"\nStats: kept={kept_count}, blocked_by_requirements={skipped_blocked}, skipped_no_explicit_sponsor={skipped_no_explicit}")
