# Job Application Tracker

A Flask + MySQL CRUD website for COP4751 with a dashboard, four related tables and skill-based Job Match.

## Requirements
Python 3, MySQL Server 8+, pip. All required packages are in `requirements.txt`.

## Quick start (Windows)
1. Download/extract this repository.
2. Open Command Prompt in the project folder.
3. Run `py -m pip install -r requirements.txt`.
4. In MySQL Workbench, run the full `schema.sql` **only on a new database**. If you previously created `job_tracker`, see the note below.
5. In the same Command Prompt, run `set MYSQL_PASSWORD=YOUR_OWN_MYSQL_PASSWORD` (replace with your private local password; do not commit it).
6. Run `py app.py`.
7. Open http://127.0.0.1:5000/ in your browser.

The app uses MySQL on `127.0.0.1:3306`, user `root`, database `job_tracker`. You may override `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_DATABASE` and `MYSQL_PASSWORD` environment variables. Never commit your password.

### Existing database warning
If you already created the four tables using a different schema, `CREATE TABLE IF NOT EXISTS` does not modify those tables. Back up any data first. For a clean class-project setup, you may create a fresh database by dropping the existing `job_tracker` database **only if it contains no data you need**, then execute `schema.sql`. Alternatively, migrate the old tables to match `schema.sql`.

## How to use
Create a company first, then a job, then an application or contact. Edit and delete using the table pages. Related parent records cannot be deleted until dependent records are removed. For Job Match, enter skills separated by commas. Each job's `requirements` is a JSON array of required skills; percentage = matched required skills / total required skills × 100. Jobs with no requirements score 0%.

## Demonstration checklist
Show MySQL Workbench tables, Flask terminal running, dashboard, and creating/editing/deleting records in each of the four sections. Add jobs with requirements (e.g. `Python, SQL, Flask`), run Job Match, and show the missing skills and percentages. Record a 3–7 minute video and upload the actual video file to the GitHub repository before submitting its URL.

## Testing
Manual tests: create/edit/delete a company; add job linked to company; add application linked to job; add contact linked to company; confirm dashboard totals; try an invalid empty required field; check job match 2/3 = 67%; verify deleting a parent with children displays a warning. These tests must be run locally with MySQL; packaging the source code does not prove they passed.
