#####################################################################
# cloudsync is a simple python script using NetApp Cloud Rest API
# jerome.blanchet@netapp.com
#####################################################################
import netapp_api_cloud
import argparse
import getpass
import sys
import configparser
import json
import os

RELEASE='0.3'
#####################################################################
# Local API 
#####################################################################
Debug = False

def print_vers():
      print (RELEASE)

def print_syntax_error(mess):
      print ('ERROR: {0}'.format(mess))

def print_deb (debug_var):
    if (Debug):
        print("DEBUG: [", end="") 
        print(debug_var,end="]\n")

#####################################################################
# API Configuration file 
#####################################################################
from sys import platform
if (platform == "win32") :
    print_deb("Another Win32 system")
    username=os.environ.get('username')
    homedrive=os.environ.get('homedrive')
    homepath=os.environ.get('homepath')
    API_DIR=homedrive + homepath + "\\NetAppCloud"
    API_CONFIG_FILE= API_DIR + '\\api.conf'
else:
    USER=os.environ.get('USER')
    HOME=os.environ.get('HOME')
    API_DIR= HOME  + "/NetAppCloud"
    API_CONFIG_FILE= API_DIR + '/api.conf'

if ( os.path.isdir(API_DIR) != True ):
    os.mkdir(API_DIR)

#####################################################################
# Main
#####################################################################
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", dest='debug', help="debug mode", action="store_true")
parser.add_argument("--account-id", dest='account_id', help="select NetApp Cloud account ID")
parser.add_argument("-j", "--json", dest='json', help="print in json format", action="store_true")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--account-list", dest='account_list', help="print cloudsnyc accounts", action="store_true" )
group.add_argument("--data-broker-list", dest='databroker_list', help="print cloudsync data-brokers", action="store_true" )
group.add_argument("--create-relation", dest='create_relation_file', help="create new cloudsync relation from json file" )
group.add_argument("--delete-relation", dest='delete_relation_id', help="delete a cloudsync relation" )
group.add_argument("--sync-relation", dest='sync_relation_id', help="sync a cloudsync relation" )
group.add_argument("--print-relations", dest='print_relations', help="print cloudsnyc relations list", action="store_true" )
group.add_argument("--check-token", dest='check_token', help="check NetApp Cloud access token", action="store_true" )
group.add_argument("--get-new-token", dest='get_new_token', help="get a new access token", action="store_true" )
args = parser.parse_args()

if args.debug:
      Debug = True
      netapp_api_cloud.Debug = True 

try:
    file_info = netapp_api_cloud.check_API_config_file(API_CONFIG_FILE)
    if ( file_info["status"] != "success" ):
         print("ERROR: {0}".format(file_info["message"]))
         exit(1)

    if args.get_new_token:
         # Create a new token
         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
    else: 
         # Get Token and cloud manager account informations 
         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)

    API_TOKEN=token_info["token"]

    print_deb("API_TOKEN: {0}".format(API_TOKEN))

    # Get Account Information from the config file
    account_info=netapp_api_cloud.get_default_account(API_CONFIG_FILE)
    if (account_info["status"] == "success"):
         account_id = account_info["default_account_id"] 
    else:
         account_id = ""

    # args options 
    if args.account_id:
         account_id = args.account_id 

    if args.account_list:

         default_account_id = account_id 
         print("Print NetApp Account list:")
         accounts_info=netapp_api_cloud.cloudsync_get_accounts_list(API_TOKEN)
         print_deb(accounts_info)

         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              for account in accounts:
                   if ( account["accountId"] == default_account_id ):
                        print("Name:[{0}] account_id:[{1}] Default:[X]".format(account["name"], account["accountId"]))
                   else:
                        print("Name:[{0}] account_id:[{1}] Default:[ ]".format(account["name"], account["accountId"]))

    if args.databroker_list:

         if ( account_id != "" ):
              databrokers_info=netapp_api_cloud.cloudsync_get_databrokers_list(API_TOKEN, account_id)
              print_deb(databrokers_info)

              if (databrokers_info["status"] == "success"):
                   databrokers=json.loads(databrokers_info["databrokers"])
                   if (args.json):
                        print(json.dumps(databrokers, indent=4))
                   else:
                        print("Print NetApp data-borkers list:")
                        for databroker in databrokers:
                             print("Name:[{0}] ID:[{1}] PrivateIP:[{2}] TransferRate:[{3}] Status:[{4}] ".format(databroker["name"], databroker["id"],databroker["placement"]["privateIp"], databroker["transferRate"],databroker["status"]))
         else:
              print("ERROR: Syntaxe : miss account_id ")
              exit(1)

    if args.print_relations:

         if ( account_id != "" ):
              relations_info=netapp_api_cloud.cloudsync_get_relations(API_TOKEN, account_id)
              print_deb(relations_info)
              if (relations_info["status"] == "success"):
                   relations=json.loads(relations_info["relations"])
                   if (args.json):
                        print(json.dumps(relations, indent=4))
                   else:  
                        print("Print cloudsync relations:") 
                        for relation in relations:
                             activity=relation["activity"]
                             print("")
                             print("id: {0}".format(relation["id"]))
                             print("account: {0}".format(relation["account"]))
                             print("dataBroker: {0}".format(relation["dataBroker"]))
                             print("source: {0}".format(relation["source"]))
                             print("target: {0}".format(relation["target"]))
                             print("type: {0}".format(activity["type"]))
                             print("status: {0}".format(activity["status"]))
                             print("status: {0}".format(activity["progress"]))
                             print("")
         else: 
             print("ERROR: Syntaxe : miss account_id ")
             exit(1)

    if args.create_relation_file:
         if ( account_id != "" ):
              print("create new cloudsnyc relation form json file: {0}".format(args.create_relation_file))
              if (os.path.isfile(args.create_relation_file) != True ):
                  print("Error: {0} : file not found".format(args.create_relation_file))
                  exit(1)
              f = open(args.create_relation_file)
              new_relation_json=json.load(f)
              print_deb(new_relation_json)
              f.close

              relations_info=netapp_api_cloud.cloudsync_create_relations(API_TOKEN, account_id, new_relation_json)
              if (relations_info["status"] == "success"):
                   print("New cloud Sync relationship successfully created")
              else:
                   print("ERROR: {0}".format(relations_info["message"]))
         else: 
             print("ERROR: Syntaxe : miss account_id ")
             exit(1)

    if args.sync_relation_id:

         if ( account_id != "" ):
              print("Sync cloudsync relation ID: {0}".format(args.sync_relation_id))
              relation_info=netapp_api_cloud.cloudsync_sync_relation(API_TOKEN, account_id,args.sync_relation_id)
              if (relation_info["status"] != "success"):
                   print_deb(relation_info["status"])
                   print("ERROR: {0}".format(relation_info["message"]))
         else: 
             print("ERROR: Syntaxe : miss account_id ")
             exit(1)


    if args.delete_relation_id:

         if ( account_id != "" ):
              print("Delete cloudsync relation ID: {0}".format(args.delete_relation_id))
              relation_info=netapp_api_cloud.cloudsync_delete_relation(API_TOKEN, account_id,args.delete_relation_id)
              if (relation_info["status"] != "success"):
                   print_deb(relation_info["status"])
                   print("ERROR: {0}".format(relation_info["message"]))
         else: 
             print("ERROR: Syntaxe : miss account_id ")
             exit(1)

    if args.check_token:
         # Get Token and cloud manager account informations 
         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] == "unknown" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
         print("Access Token is valid")
         exit(0)

except KeyboardInterrupt:
    print ("exit")
    exit(0)