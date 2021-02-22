# Splunk Dashboards/Forms XML To CSV

Traverse all Splunk's dir dashboards/forms xml files (in, current folder or nested folders level), and generate a CSV file of all individual panels with the following details:

- Source File	
- Dashboard Name	
- Panel Type	
- Panel Name	
- Search Type	
- Splunk Query	
- Sumo Query

## <u>Usage</u>

- `python3 orgs_contents_diff.py`
- Enter Source/Destination region of deployment 
- Enter Source/Destination API's credentials such as AccessId/AccessKey

### <u>Process</u>

The script will report on the overall and per user progress and then generate and open a CSV report.