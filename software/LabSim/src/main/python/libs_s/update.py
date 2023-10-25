# -*- coding: utf-8 -*-
"""
Update the LabSim software.
download list of files from GitHub with md5 checksum
and verify local files with md5 checksum, 
remove old locals file and replace with files dowlnoaded from GitHub
"""

import requests


def download_md5_list(url, local_file):
    """
    Download md5 list from GitHub and save it to local_file
    """
    r = requests.get(url)
    with open(local_file, 'wb') as f:
        f.write(r.content)
        
