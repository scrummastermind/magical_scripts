import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import pprint
import time
import subprocess
import re
import collections
import os


counter = 1
user_counter = 0
total_steps = 0
sub_count = 0
sub_total_steps = 1
num_of_users_source = 0

def printSubProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def content_item_to_path(source_region, dest_region, base_urls, headers, auths, name, content, loggedin, sub_prefix='', global_folder_name=''):
    paths = []
    global counter
    global user_counter
    global total_steps
    global sub_total_steps
    global sub_count
    global num_of_users_source
    if isinstance(content, dict):
        if 'id' in content and 'name' in content and 'itemType' in content:
            id = content['id']
            name = content['name']
            itemType = content['itemType']
            description = 'N/A'
            if 'description' in content.keys():
                description = content['description']
                m = re.search('\((.*)\)', description)
                if m:
                    description = m.group(1).strip()

            content_path = requests.get(base_urls[source_region] + 'v2/content/' + str(id) + "/path", headers=headers, auth=auths[source_region])
            content_path_json = json.loads(content_path.text)
            currentPath = content_path_json['path']
            params = {'path': potential_dest_path}
            dest_content_path_response = requests.get(base_urls[dest_region] + 'v2/content/path', headers=headers, auth=auths[dest_region], params=params)
            
            dest_id = 'N/A'


            if loggedin:
                dest_content_status_code = dest_content_path_response.status_code
                dest_content = json.loads(dest_content_path_response.text)
                if str(dest_content_status_code) == '200' and 'id' in dest_content.keys():
                    dest_id = dest_content['id']
                elif str(dest_content_status_code) == '404' and 'errors' in dest_content.keys():
                    dest_id = 'Missing'
                else:
                    dest_id = 'Othe error'
            else:
                dest_id='User never logged in'

            
            
            details = {'id': id, 'name': name, 'itemType': itemType,
                       'path': currentPath, 'email':  description, 'logged-in': loggedin, 'content-id-dest': dest_id}
            counter += 1
            os.system('clear')
            print("Analysing the contents of {} users from the source\n".format(num_of_users_source))
            sub_prefix = 'User # ' + str(user_counter) + ' - (' + \
                global_folder_name + ') - '
            global_prefix = 'Global Progress:'
            printProgressBar(counter, total_steps, prefix=global_prefix, suffix='Complete\n', length=150)
            
            if sub_count == 0:
                print(sub_prefix + 'No contents found!')
            else:
                subPrefix = sub_prefix + \
                    str(sub_count) + ' contents so far ' + 'Progress:'
                printSubProgressBar(sub_count, max(1, sub_total_steps), prefix=subPrefix,
                                    suffix='Complete', length=(150+len(global_prefix))-len(subPrefix))

            sub_count += 1
            paths.append(details)
            if itemType == 'Folder' and 'children' in content and len(content['children']) > 0:
                children_len = len(content['children'])
                total_steps += children_len
                sub_total_steps+=children_len
                for child in content['children']:
                    if child['itemType'] == 'Folder':
                        child_response = requests.get(base_urls[source_region] + 'v2/content/folders/' + str(child['id']), headers=headers, auth=auths[source_region])
                        child = json.loads(child_response.text)
                    paths=paths + content_item_to_path(source_region, dest_region, base_urls, headers, auths,
                                                       name, child, loggedin,sub_prefix=sub_prefix, global_folder_name=global_folder_name)

    elif isinstance(content, list):
        for _ , item in enumerate(content):
            paths = paths + content_item_to_path(source_region, dest_region, base_urls, headers,
                                                 auths, name, item, loggedin, sub_prefix=sub_prefix, global_folder_name=global_folder_name)

    return paths

def get_global_folders(region, base_urls, headers, auths):
	global_folders_job_response = requests.get(base_urls[region] + 'v2/content/folders/global', headers = headers, auth = auths[region])
	global_folders_job_json = json.loads(global_folders_job_response.text)
	global_folders_job_id = global_folders_job_json['id']
	global_folders_job_status = ''

	while global_folders_job_status != 'Success':
		global_folders_job_status_response = requests.get(base_urls[region] + "v2/content/folders/global/{}/status".format(global_folders_job_id), headers = headers, auth = auths[region])
		global_folders_job_status_json = json.loads(global_folders_job_status_response.text)
		global_folders_job_status = global_folders_job_status_json['status']

	global_folders_job_status_result_response = requests.get(base_urls[region] + "v2/content/folders/global/{}/result".format(global_folders_job_id), headers = headers, auth = auths[region])
	global_folders_job_status_result_json = json.loads(global_folders_job_status_result_response.text)

	global_folders = {folder['name']:folder['id'] for folder in global_folders_job_status_result_json['data']}

	return global_folders


def main():
    global total_steps
    global counter
    global user_counter
    global sub_total_steps
    global sub_count
    global num_of_users_source
    regions = ['DEST', 'SRC']
    missing_folders_withcontents = []
    base_urls = {'DEST': 'https://api.eu.sumologic.com/api/', 'SRC': 'https://api.sumologic.com/api/'}
    headers = {'isAdminMode': 'true'}
    destAccessId = input("Enter DEST Sumo Org Access Id: ")
    destAccessKey = input("Enter DEST Sumo Org Access Key: ")
    srcAccessId = input("Enter SRC Sumo Org Access Id: ")
    srcAccessKey = input("Enter SRC Sumo Org Access Key: ")
    auths = {'DEST': HTTPBasicAuth(destAccessId, destAccessKey), 'SRC': HTTPBasicAuth(
        srcAccessId, srcAccessKey)}
    global_folders = {}

    for region in regions:
        global_folders[region] = collections.OrderedDict(sorted(get_global_folders(region, base_urls, headers, auths).items()))

    num_of_users_source=len(global_folders['SRC'].keys())
    total_steps = num_of_users_source
    os.system('clear')
    print("Analysing the contents of {} users from the source\n".format(num_of_users_source))
    user_counter = 1
    for global_folders_name in global_folders['SRC'].keys():
        sub_count = 0
        they_logged_in_to_dest = global_folders_name in global_folders['DEST'].keys()
        us_folder_response = requests.get(base_urls['SRC'] + "v2/content/folders/{}".format(global_folders['SRC'][global_folders_name]), headers = headers, auth = auths['SRC'])
        us_folder_result = json.loads(us_folder_response.text)
        sub_total_steps = len(us_folder_result['children'])
        rows=content_item_to_path('SRC', 'DEST', base_urls, headers, auths, global_folders_name, us_folder_result,
                                  they_logged_in_to_dest, sub_prefix='', global_folder_name=global_folders_name)
        missing_folders_withcontents = missing_folders_withcontents + rows
        counter+=1
        user_counter+=1

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = "missing_folders_withcontents_{}".format(timestr)
    json_file_name = file_name + '.json'
    csv_file_name = file_name + '.csv'
    with open(json_file_name, 'w') as outfile:
        json.dump(missing_folders_withcontents, outfile)

    df = pd.read_json(json_file_name)
    df.sort_values("path", axis=0, ascending=True,
                 inplace=True, na_position='last')
    df.to_csv(csv_file_name, index=False)
    subprocess.check_output(['open', csv_file_name])

if __name__ == "__main__":
    main()
