import sys
import os
import re
import subprocess
import csv
import xml.etree.ElementTree as ET
from pprint import pprint


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return " ".join([m.group(0).capitalize() for m in matches])

def rex_to_parse_regex(query):
    return re.sub(r'\|\s*rex\s+(field\s*=\S+)?\s+(.*)', r'| parse regex \1 "\2" nodrop', query)

def replace_headers(query, old, new):
    return query.replace(old, new)
    

def main():
  csv_rows = []
  for root, dirs, files in os.walk("."):
      for file in files:
          src_file = (os.path.join(root, file))
          if src_file.endswith('.xml'):
            etree = ET.parse(src_file)
            dashboard_xml_root = etree.getroot()
            all_tags = [elem.tag for elem in dashboard_xml_root.iter()]

            if not ('panel' in all_tags and ('dashboard' in all_tags or 'form' in all_tags)):
              continue

            label = dashboard_xml_root.find('label')

            for panel in dashboard_xml_root.iter('panel'):
              row = {}
              panel_type_tag =''
              dash_name = ''
              title = ''
              query=''

              for elem in panel.iter():
                if elem.tag in ('chart','event','html','map','single','table','viz'):
                  panel_type_tag = elem.tag
                  break

              if panel_type_tag in ('html'):
                continue

              if label!=None:
                dash_name = label.text
         
              if panel.find('title')!=None:
                title = panel.find('title').text

              panel_type = panel.find(panel_type_tag)
              query = ''
              search_type = ''

              for search_panel_type in panel_type.iter():
                if search_panel_type.tag in ('search','searchTemplate', 'searchString', 'searchName'):
                  search_type = search_panel_type.tag
                  if search_panel_type.tag == 'search' and panel.find(panel_type_tag).find('search')!=None:
                    search_elem = panel.find(panel_type_tag).find('search')
                    if search_elem.find('query')!=None:
                        query = search_elem.find('query').text
                    elif 'ref' in search_elem.attrib.keys():
                      query = search_elem.attrib['ref']
                  elif search_panel_type.tag == 'searchTemplate' and panel.find(panel_type_tag).find('searchTemplate')!=None:
                    query = panel.find(panel_type_tag).find('searchTemplate').text
                  elif search_panel_type.tag == 'searchString' and panel.find(panel_type_tag).find('searchString')!=None:
                    query = panel.find(panel_type_tag).find('searchString').text
                  elif search_panel_type.tag == 'searchName' and panel.find(panel_type_tag).find('searchName')!=None:
                    query = panel.find(panel_type_tag).find('searchName').text

              if title==''  and panel.find(panel_type_tag)!=None and panel.find(panel_type_tag).find('title')!=None:
                title = panel.find(panel_type_tag).find('title').text

              query = str(query)
              splunk_query = re.sub(r"\s*\|\s*", "\n| ", query)
              sumo_query = rex_to_parse_regex(splunk_query)
           
              row['Source File'] = src_file
              row['Dashboard Name'] = dash_name
              row['Panel Type'] = panel_type_tag.capitalize()
              row['Panel Name'] = title
              row['Search Type'] = camel_case_split(search_type)
              row['Splunk Query'] = splunk_query
              row['Sumo Query'] = sumo_query

              csv_rows.append(row)
  if len(csv_rows) > 0:
    columns = csv_rows[0].keys()
    with open('results.csv', 'w', newline='')  as output_file:
      dict_writer = csv.DictWriter(output_file, columns)
      dict_writer.writeheader()
      dict_writer.writerows(csv_rows)
    subprocess.check_output(['open', 'results.csv'])

if __name__ == "__main__":
    main()


