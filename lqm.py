#!/usr/bin/env python3

# 20201020 - Add a function to add a single prefix to a local prefixlist - Dan
import cloudgenix
import argparse
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
import sys
import logging
import os
import datetime
import collections
import csv
from csv import DictReader
import time
from datetime import datetime, timedelta
jdout = cloudgenix.jdout


# Global Vars
TIME_BETWEEN_API_UPDATES = 60       # seconds
REFRESH_LOGIN_TOKEN_INTERVAL = 7    # hours
SDK_VERSION = cloudgenix.version
SCRIPT_NAME = 'CloudGenix: Example script: LQM Apps'
SCRIPT_VERSION = "v1"
directory = 'path_data'

# Set NON-SYSLOG logging to use function name
logger = logging.getLogger(__name__)


####################################################################
# Read cloudgenix_settings file for auth token or username/password
####################################################################

sys.path.append(os.getcwd())
try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes network.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None

try:
    from cloudgenix_settings import CLOUDGENIX_USER, CLOUDGENIX_PASSWORD

except ImportError:
    # will get caught below
    CLOUDGENIX_USER = None
    CLOUDGENIX_PASSWORD = None


def deploy(cgx, site_name, csv):
    file_exists = os.path.exists(csv)
    if not file_exists:
        print("File " + csv + " does not exsists")
        return
    app_list = []
    app_n2id = {}
    for apps in cgx.get.appdefs().cgx_content["items"]:
        app_n2id[apps['display_name']] = apps['id']


    with open(csv, 'r') as read_obj:
        csv_dict_reader = DictReader(read_obj)
        for row in csv_dict_reader:
            apps = {}
            apps = row
            try:
                lqm_latency = None
                lqm_latency = int(apps["latency"])
            except:
                print ('Error please correct latency value for ' + str(apps["app_name"]))
                return
            try:
                lqm_loss = None
                lqm_loss = int(apps["loss"])
            except:
                try:
                    lqm_loss = None
                    lqm_loss = float(apps["loss"])
                    loss_check = False
                except:
                    print ('Error please correct loss value for ' + apps["app_name"])
                    return
            try:
                lqm_jitter = None
                lqm_jitter = int(apps["jitter"])
            except:
                print ('Error please correct jitter value for ' + str(apps["app_name"]))
                return
            try:
                apps['id'] = app_n2id[apps["app_name"]]
            except:
                print ("Error " + apps["app_name"] + " does not exsist please check the name")
                return
            app_list.append(apps)
    
    if site_name == "ALL_SITES":
        print ("Creating/Updating LQM Apps for all sites\n")
    else:
        print ("Creating/Updating LQM Apps on site " + site_name +  "\n")
    for site in cgx.get.sites().cgx_content["items"]:
        site_check = False
        if site_name == "ALL_SITES":
            site_check = True
        elif site_name == site['name']:
            site_check = True
        if site["element_cluster_role"] != "SPOKE":
            site_check = False
        if site_check:
            for element in cgx.get.elements().cgx_content["items"]:
                if element["site_id"] == site["id"]:
                    for app_check in app_list:
                        if app_check['loss'] == '0':
                            loss_enabled = False
                        else:
                            loss_enabled = True
                        if app_check['latency'] == '0':
                            latency_enabled = False
                        else:
                            latency_enabled = True
                        if app_check['jitter'] == '0':
                            jitter_enabled = False
                        else:
                            jitter_enabled = True
                
                        create_lqm = True
                        name_check = app_check['app_name'] + "-LQM"
                        for item in cgx.get.element_extensions(site_id = site["id"], element_id = element["id"]).cgx_content["items"]:
                            if name_check == item["name"]:
                                create_lqm = False
                                update_lqm = False
                                if item["conf"]['packet_loss'] != app_check['loss'] or item["conf"]['packet_loss_en'] != loss_enabled:
                                    item["conf"]['packet_loss'] = app_check['loss']
                                    item["conf"]['packet_loss_en'] = loss_enabled
                                    update_lqm = True
                                if item["conf"]['latency'] != app_check['latency'] or item["conf"]['latency_en'] != latency_enabled:
                                    item["conf"]['latency'] = app_check['latency']
                                    item["conf"]['latency_en'] = latency_enabled
                                    update_lqm = True
                                if item["conf"]['jitter'] != app_check['jitter'] or item["conf"]['jitter_en'] != jitter_enabled:
                                    item["conf"]['jitter'] = app_check['jitter']
                                    item["conf"]['jitter_en'] = jitter_enabled
                                    update_lqm = True
                                if update_lqm:
                                    resp = cgx.put.element_extensions(site_id = site["id"], element_id = element["id"], extension_id=item['id'], data=item)
                                    if not resp:
                                        print ("Error updating LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'])
                                    else:
                                        print ("Updating LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'])
                                else:
                                    print ("LQM " + app_check['app_name'] + " already created on site " + site['name'] + " ION " + element['name'])
                        if create_lqm:
                            data = {"name": name_check, "namespace": "thresholds/lqm/app", "entity_id": app_check['id'], "disabled": False, "conf": {"latency": app_check['latency'], "latency_en": True, "jitter": "0", "jitter_en": False, "packet_loss": app_check['loss'], "packet_loss_en": True}}
                            resp = cgx.post.element_extensions(site_id = site["id"], element_id = element["id"], data=data)
                            if not resp:
                                print ("Error creating LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'])
                                print (str(jdout(resp)))
                            else:
                                print ("Creating LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'])

def destroy(cgx, site_name, csv):
    file_exists = os.path.exists(csv)
    if not file_exists:
        print("File " + csv + " does not exsists")
        return
    app_list = []
    app_n2id = {}
    for apps in cgx.get.appdefs().cgx_content["items"]:
        app_n2id[apps['display_name']] = apps['id']


    with open(csv, 'r') as read_obj:
        csv_dict_reader = DictReader(read_obj)
        for row in csv_dict_reader:
            apps = {}
            apps = row
            try:
                lqm_latency = None
                lqm_latency = int(apps["latency"])
            except:
                print ('Error please correct latency value for ' + str(apps["app_name"]))
                return
            try:
                lqm_loss = None
                lqm_loss = int(apps["loss"])
            except:
                try:
                    lqm_loss = None
                    lqm_loss = float(apps["loss"])
                    loss_check = False
                except:
                    print ('Error please correct loss value for ' + apps["app_name"])
                    return
            try:
                apps['id'] = app_n2id[apps["app_name"]]
            except:
                print ("Error " + apps["app_name"] + " does not exsist please check the name")
                return
            app_list.append(apps)
    if site_name == "ALL_SITES":
        print ("Deleting LQM Apps for all sites\n")
    else:
        print ("Deleting LQM Apps on site " + site_name +  "\n")
    for site in cgx.get.sites().cgx_content["items"]:
        site_check = False
        if site_name == "ALL_SITES":
            site_check = True
        elif site_name == site['name']:
            site_check = True
        if site["element_cluster_role"] != "SPOKE":
            site_check = False
        if site_check:
            for element in cgx.get.elements().cgx_content["items"]:
                if element["site_id"] == site["id"]:
                    for item in cgx.get.element_extensions(site_id = site["id"], element_id = element["id"]).cgx_content["items"]:
                        for app_check in app_list:
                            name_check = app_check['app_name'] + "-LQM"
                            if name_check == item["name"]:
                                resp = cgx.delete.element_extensions(site_id = site["id"], element_id = element["id"], extension_id=item['id'])
                                if not resp:
                                    print ("Error deleteing LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'] + '. Download log for details..')
                                    print (str(jdout(resp)))
                                else:
                                    print ("Deleting LQM " + app_check['app_name'] + " on site " + site['name'] + " ION " + element['name'])
                                      
def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))
    
    config_group = parser.add_argument_group('Config', 'These options change how the configuration is generated.')
    config_group.add_argument('--sites', '-S',
                                  help='Site name or special string "ALL_SITES".',
                                  required=True)
    config_group.add_argument('--file', '-F',
                                  help='CSV File for Apps with app_name, latency and loss',
                                  required=False)
    config_group.add_argument('--delete', '-D',
                                  help='Delete Apps LQM settings',
                                  default=False)

    # Allow Controller modification and debug level sets.
    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. "
                                       "Alpha: https://api-alpha.elcapitan.cloudgenix.com"
                                       "C-Prod: https://api.elcapitan.cloudgenix.com",
                                  default=None)
    controller_group.add_argument("--insecure", "-I", help="Disable SSL certificate and hostname verification",
                                  dest='verify', action='store_false', default=True)
    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')
    login_group.add_argument("--email", "-E", help="Use this email as User Name instead of prompting",
                             default=None)
    login_group.add_argument("--pass", "-PW", help="Use this Password instead of prompting",
                             default=None)
    debug_group = parser.add_argument_group('Debug', 'These options enable debugging output')
    debug_group.add_argument("--debug", "-DE", help="Verbose Debug info, levels 0-2", type=int,
                             default=0)
    
    args = vars(parser.parse_args())
                             
    ############################################################################
    # Instantiate API
    ############################################################################
    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=args["verify"])

    # set debug
    cgx_session.set_debug(args["debug"])

    ##
    # ##########################################################################
    # Draw Interactive login banner, run interactive login including args above.
    ############################################################################
    print("{0} v{1} ({2})\n".format(SCRIPT_NAME, SCRIPT_VERSION, cgx_session.controller))

    # login logic. Use cmdline if set, use AUTH_TOKEN next, finally user/pass from config file, then prompt.
    # figure out user
    if args["email"]:
        user_email = args["email"]
    elif CLOUDGENIX_USER:
        user_email = CLOUDGENIX_USER
    else:
        user_email = None

    # figure out password
    if args["pass"]:
        user_password = args["pass"]
    elif CLOUDGENIX_PASSWORD:
        user_password = CLOUDGENIX_PASSWORD
    else:
        user_password = None

    # check for token
    if CLOUDGENIX_AUTH_TOKEN and not args["email"] and not args["pass"]:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()

    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None

    ############################################################################
    # End Login handling, begin script..
    ############################################################################

    # get time now.
    curtime_str = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')

    # create file-system friendly tenant str.
    tenant_str = "".join(x for x in cgx_session.tenant_name if x.isalnum()).lower()
    
    site_name = args['sites']
    csv = args['file']
    delete = args['delete']
    cgx = cgx_session
    if delete:
        destroy(cgx, site_name, csv)
    else:
        deploy(cgx, site_name, csv)
    
    # end of script, run logout to clear session.
    cgx_session.get.logout()

if __name__ == "__main__":
    go()