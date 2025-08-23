# main.py (FINAL VERSION - With Excel Export)
import os
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
# We will save the output file inside your 'Output' folder
EXCEL_OUTPUT_FILE = "Output/found_jobs.xlsx"


# --- Part 2: HELPER FUNCTIONS ---

def load_existing_job_ids(file_path):
    """Loads job IDs from an existing Excel file to prevent duplicates."""
    if not os.path.exists(file_path):
        return set()
    try:
        df = pd.read_excel(file_path)
        return set(df['Job ID'].tolist())
    except (FileNotFoundError, KeyError):
        return set()

def save_jobs_to_excel(jobs_list, file_path):
    """Creates or appends a list of jobs to an Excel file."""
    if not jobs_list:
        return
        
    # Define the columns we want in our Excel file and their order
    columns = {
        'job_id': 'Job ID', 'job_title': 'Title', 'employer_name': 'Company',
        'job_city': 'City', 'job_state': 'State', 'job_apply_link': 'Application Link'
    }
    
    new_jobs_df = pd.DataFrame(jobs_list)[list(columns.keys())].rename(columns=columns)

    if os.path.exists(file_path):
        # Append to existing file without writing the header again
        with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            existing_df = pd.read_excel(file_path)
            new_jobs_df.to_excel(writer, startrow=len(existing_df) + 1, header=False, index=False)
    else:
        # Create a new file
        # Ensure the 'Output' directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        new_jobs_df.to_excel(file_path, index=False)


def find_jobs(query):
    """Searches for jobs using the JSearch API."""
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
    params = {"query": f"entry level to mid level {query} in USA", "num_pages": "1"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException:
        return []

# --- Part 3: MAIN EXECUTION ---
if __name__ == "__main__":
    
    # Load IDs of jobs we've already saved
    existing_job_ids = load_existing_job_ids(EXCEL_OUTPUT_FILE)
    print(f"Found {len(existing_job_ids)} jobs already in '{EXCEL_OUTPUT_FILE}'.")
    
    new_jobs_to_save = []

    print("\n--- Starting Targeted Job Search ---")
    
    for job_title in TARGET_JOB_TITLES:
        print(f"Searching for: '{job_title}'...")
        jobs_from_api = find_jobs(job_title)
        
        for job in jobs_from_api:
            job_id = job.get('job_id')
            if job_id and job_id not in existing_job_ids:
                new_jobs_to_save.append(job)
                existing_job_ids.add(job_id) # Add to set to avoid duplicates within the same run
        
        time.sleep(1) # Be polite to the API

    # --- After all searches are complete, save and report results ---
    if new_jobs_to_save:
        print(f"\n--- Found {len(new_jobs_to_save)} new job openings! ---")
        save_jobs_to_excel(new_jobs_to_save, EXCEL_OUTPUT_FILE)
        print(f"All new jobs have been saved to '{EXCEL_OUTPUT_FILE}'")
        
        # Optionally print new jobs to console as well
        for i, job in enumerate(new_jobs_to_save[:10], 1): # Print first 10 new jobs
             print(f"  -> New job added: {job.get('job_title')} at {job.get('employer_name')}")
    else:
        print(f"\n--- No new job openings found. Your list in '{EXCEL_OUTPUT_FILE}' is up to date. ---")