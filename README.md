**JOB_FETCH_PROJECT**

**A simple Python project that helps you fetch the latest job postings (entry-level to mid-level) from the JSearch API  and store them neatly into an Excel file**
- Every time you run the script, it:

    Searches for jobs by your target job titles (defined inside main.py).
    Avoids duplicates by checking against jobs already saved.
    Appends new jobs into an Excel file for easy tracking.


## set up instructions

1. Clone or download this repository
        `git clone <your-repo-url>`
        `cd JOB_FETCH_PROJECT`

2. Create and activate a virtual environment
        `python -m venv venv`
        `venv\Scripts\activate` - winndows 
        `source venv/bin/activate` - Linux

3. Install dependencies
        `pip install -r requirements.txt`

4. Set up your API key
    - Sign up on RapidAPI and subscribe to the JSearch API.
    - Copy your API key.
    - Create a .env file in the project root and add:
            `RAPIDAPI_KEY=your_api_key_here`

5. Running the Script
    - Once everything is set up, simply run:
    `python main.py`

6. expected output:
    - The script will print progress in the console.
    - Results are saved into Output/found_jobs.xlsx.
    - If the file already exists, only new jobs are appended.

-----------------------------------------------------------------------------------------------------------------------------------------------------

**You can customize this list in the TARGET_JOB_TITLES variable inside main.py.**

**Tech Stack**
- Python
- pandas – for Excel handling
- requests – for API calls
- dotenv – for environment variable management
- openpyxl – for working with Excel files

**Future Improvements**
 - Add filters (remote jobs, full-time, specific states).
 - Export results to CSV/JSON in addition to Excel.
 - Add logging for better monitoring.

**Important Notes**
 - Be mindful of API rate limits. The script includes a short delay (time.sleep(1)) between requests.
 - Always keep your .env file private (never commit it to GitHub).