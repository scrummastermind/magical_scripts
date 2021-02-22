# Sumo Orgs' Contents Diff

Traverse the contents (i.e. Dashboards, Lookups, Searches and Scheduled Searches) on a source Sumo Logic org, then deep compare 

- Whether the user in question ever logged in to the destination using the same e-mail
- If they did, whether their source org's contents exist or missing under the same path on the destination.

**Pre-requisites:** Admin level API's credentials AccessId/AccessKey to run this tool to use Admin Mode access to view all users' contents.

## <u>Install</u>

- Pull the repository, and change folder to `/SumoLogic` 
- Optional: Create Python venv:
  - Running `python3 -m venv sumovenv`
  - `source sumovenv/bin/activate`
- Run `pip install -r requirements.txt in`



## <u>Usage</u>

- `python3 orgs_contents_diff.py`
- Enter Source/Destination region of deployment 
- Enter Source/Destination API's credentials such as AccessId/AccessKey

### <u>Process</u>

The script will report on the overall and per user progress and then generate and open a CSV report.