# Prisma SD-WAN LQM Apps (Preview)
The purpose of this script to set the LQM thresholds (loss, latency and jitter) for list of Apps in a CSV  

#### Features
 - ./lqm.py can be used to set or delete the LQM thresholds (loss, latency and jitter) based off a CSV file

#### License
MIT

#### Requirements
* Active CloudGenix Account - Please generate your API token and add it to cloudgenix_settings.py
* Python >=3.7
* CSV Files with a app_name, latency, loss and jiter column headers

#### Installation:
 Scripts directory. 
 - **Github:** Download files to a local directory, manually run the scripts. 
 - pip install -r requirements.txt

### Examples of usage:
 Please generate your API token and add it to cloudgenix_settings.py
 
 - Your CSV file must contain column headers app_name, latency, loss and jitter
 - If you set any of the latency, loss or jitter values to 0 they will be enabled
 
 - Update ALL-SITES LQM thresholds from a CSV
 1. ./lqm.py -S ALL_SITES -F lqm_apps.csv
 
 - Update Branch-Site1 LQM thresholds from a CSV
 1. ./lqm.py -S Branch-Site1 -F lqm_apps.csv
 
 - Delete ALL-SITES LQM thresholds from a CSV
 1. ./lqm.py -S Branch-Site1 -D True -F lqm_apps.csv
      - -F is the CSV file and -V is the ION code

 
### Caveats and known issues:
 - This is a PREVIEW release, hiccups to be expected. Please file issues on Github for any problems.

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SD-WAN Documentation at <https://docs.paloaltonetworks.com/prisma/cloudgenix-sd-wan.html>
