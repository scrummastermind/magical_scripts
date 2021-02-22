import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import pprint
import time
import subprocess
import re
import collections
from collections import deque
from queue import LifoQueue
import os


sub_count = 0
sub_total_steps = 0
user_counter = 0
global_folder_name = ''
num_of_users_source = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
    print(f'\r{bcolors.WARNING}{prefix}{bcolors.ENDC} |{bcolors.OKGREEN}{bar}{bcolors.ENDC}| {bcolors.OKCYAN}{percent}{bcolors.ENDC}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def content_item_to_path(source_region, dest_region, base_urls, headers, auths, id, loggedin):
    paths = []
    details = {}
    global user_counter
    global global_folder_name
    global num_of_users_source
    global sub_count
    global sub_total_steps
    children_response = requests.get(
        base_urls[source_region] + 'v2/content/folders/' + str(id), headers=headers, auth=auths[source_region])
    children_contents = json.loads(children_response.text)
    id = children_contents['id']
    name = children_contents['name']
    itemType = children_contents['itemType']
    description = children_contents['description']
    content_children = children_contents['children']
    children_count = len(content_children)
    sub_total_steps+=children_count 
    updateProgress()
    if description:
        m = re.search('\((.*)\)', description)
        if m:
            description = m.group(1).strip()

    if children_count==0:
        details = processItemPath(base_urls, source_region, id, headers,
                              auths, loggedin, dest_region, name, itemType, description)
        paths.append(details)
    else:
        for child in content_children:
            sub_count+=1
            id = child['id']
            name = child['name']
            itemType = child['itemType']
            description = ''
            if itemType == 'Folder':
                id = child['id']
                paths = paths + content_item_to_path(source_region, dest_region, base_urls, headers, auths, id, loggedin)

            details = processItemPath(base_urls, source_region, id, headers, auths, loggedin, dest_region, name, itemType, description)
            paths.append(details)
    return paths


def updateProgress(folder_path_display=None):
    global user_counter
    global global_folder_name
    global num_of_users_source
    global sub_count
    global sub_total_steps
    sub_prefix = ''
    os.system('clear')
    print(
        f'{bcolors.HEADER}Analysing the contents of {num_of_users_source} users from the source{bcolors.ENDC}\n')
    sub_prefix = 'User # ' + str(user_counter + 1) + ' - (' + \
        global_folder_name + ') ' 
    global_prefix = 'Global Progress:'
    
    printProgressBar(user_counter, num_of_users_source,
                        prefix=global_prefix, suffix='Complete\n\n', length=150)
    printProgressBar(sub_count, sub_total_steps,
                        prefix=sub_prefix, suffix='Complete\n\n', length=166-len(sub_prefix))
    if folder_path_display!=None:
        print("Processing full path: {}".format(folder_path_display))
    return sub_prefix

def processItemPath(base_urls, source_region, id, headers, auths, loggedin, dest_region, name, itemType, description):
    content_path = requests.get(base_urls[source_region] + 'v2/content/' + str(id) + "/path", headers=headers, auth=auths[source_region])
    content_path_json = json.loads(content_path.text)
    currentPath = content_path_json['path']
    if loggedin:
        params = {'path': currentPath}
        dest_content_path_response = requests.get(base_urls[dest_region] + 'v2/content/path', headers=headers, auth=auths[dest_region], params=params)
        dest_id = 'N/A'

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
    updateProgress(folder_path_display=details['path'])
    return details

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
    global user_counter
    global global_folder_name
    global num_of_users_source
    global current_folder_name
    global global_folder_id 
    global sub_count
    global sub_total_steps

    regions = ['SRC', 'DEST']
    missing_folders_withcontents = []
    headers = {'isAdminMode': 'true'}
    
    srcRegion = input("Enter Source Sumo region, i.e AU, CA, DE, EU, FED, IN, JP, US1, US2: ")
    srcRegion = srcRegion.lower() + '.' if srcRegion in ('AU', 'CA', 'DE', 'EU', 'FED', 'IN', 'JP', 'US2') else ''
    srcAccessId = input("Enter Source Sumo Org Access Id: ")
    srcAccessKey = input("Enter Source Sumo Org Access Key: ")
    
    destRegion = input("Enter Destination Sumo region, i.e AU, CA, DE, EU, FED, IN, JP, US1, US2: ")
    destRegion = destRegion.lower() + '.' if destRegion in ('AU', 'CA', 'DE', 'EU', 'FED', 'IN', 'JP', 'US2') else ''
    destAccessId = input("Enter Destination Sumo Org Access Id: ")
    destAccessKey = input("Enter Destination Sumo Org Access Key: ")

    srcEndPoint = 'https://api.__REGION__sumologic.com/api/'.replace('__REGION__', srcRegion)
    destEndPoint = 'https://api.__REGION__sumologic.com/api/'.replace('__REGION__', destRegion)

    print("You have entered:\nSource Org (Region: {}, AccessId:{}) API EndPoint:{})\nDestination Org (Region: {}, AccessId:{}) API EndPoint:{})\n".format(srcRegion,srcAccessId,srcEndPoint, destRegion,destAccessId, destEndPoint))
    
    base_urls = {'SRC': srcEndPoint, 'DEST': destEndPoint}

    auths = {'SRC': HTTPBasicAuth(srcAccessId, srcAccessKey), 'DEST': HTTPBasicAuth(destAccessId, destAccessKey)}

    global_folders = {}

    for region in regions:
        global_folders[region] = collections.OrderedDict(sorted(get_global_folders(region, base_urls, headers, auths).items()))
    
    num_of_users_source=len(global_folders['SRC'].keys())
    total_steps = num_of_users_source
    os.system('clear')
    print("Analysing the contents of {} users from the source\n".format(num_of_users_source))
    user_counter = 0
    for folder_name in global_folders['SRC'].keys():
        global_folder_name = folder_name
        sub_total_steps = 0
        sub_count = 0
        loggedin = folder_name in global_folders['DEST'].keys()
        id = global_folders['SRC'][folder_name]
        global_folder_id = id
        rows = content_item_to_path(
            'SRC', 'DEST', base_urls, headers, auths, id, loggedin)
        missing_folders_withcontents = missing_folders_withcontents + rows
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
