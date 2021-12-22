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

RELEASE='0.1'
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
    print_deb("Ah No - Not another Win32 system !")
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
parser.add_argument("-d", "--debug", dest='debug', help="select debug mode", action="store_true")
parser.add_argument("--account-id", dest='account_id', help="select the cloudmanager account name: ACCOUNT_NAME")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--account-list", dest='account_list', help="print cloudsnyc accounts", action="store_true" )
group.add_argument("--create-relation", dest='create_relation_file', help="create a new cloudsync relation from Json CREATE_RELATION_FILE" )
group.add_argument("--delete-relation", dest='delete_relation_id', help="delete the cloudsync relation with id DELETE_RELATION_ID" )
group.add_argument("--sync-relation", dest='sync_relation_id', help="sync the cloudsync relation with id SYNC_RELATION_ID" )
group.add_argument("--print-relations", dest='print_relations', help="print cloudsnyc relations", action="store_true" )
args = parser.parse_args()

if args.debug:
      Debug = True
      netapp_api_cloud.Debug = True 

try:
    file_info = netapp_api_cloud.check_API_config_file(API_CONFIG_FILE)
    if ( file_info["status"] != "success" ):
         print("ERROR: {0}".format(file_info["message"]))
         exit(1)

    # Get Token and cloud manager account informations 
    print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
    token_info=netapp_api_cloud.get_check_token(API_CONFIG_FILE)
    if ( token_info["status"] == "unknown" ):
         print("ERROR: {0}".format(token_info["message"]))
         exit(1)

    if ( token_info["status"] != "success" ):
         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)

    API_TOKEN=token_info["token"]

    print_deb("API_TOKEN: {0}".format(API_TOKEN))

    # args options 
    if args.account_list:
         print("Print NetApp Account list:")
         accounts_info=netapp_api_cloud.get_accounts_list(API_TOKEN)
         print_deb(accounts_info)
         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              for account in accounts:
                   print("{0} account_id: [{1}]".format(account["name"], account["accountId"]))

    if args.print_relations:
         if args.account_id :
              print("Print cloudsync relations:") 
              relations_info=netapp_api_cloud.cloudsync_get_relations(API_TOKEN, args.account_id)
              print_deb(relations_info)
              if (relations_info["status"] == "success"):
                   relations=json.loads(relations_info["relations"])
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
                        print("")
              else:
                   print("ERROR: {0}".format(relations_info["message"]))
         else: 
             print ("ERROR: Syntaxe : miss account_id ")
             exit(1)


    if args.create_relation_file:
        print("create new cloudsnyc relation form json file: {0}".format(args.create_relation_file))

    if args.sync_relation_id:
        print("Sync cloudsync relation ID: {0}".format(args.sync_relation_id))
        relation_info=netapp_api_cloud.cloudsync_sync_relations(API_TOKEN, args.account_id,args.sync_relation_id)
        if (relation_info["status"] != "success"):
                   print_deb(relation_info["status"])
                   print("ERROR: {0}".format(relation_info["message"]))

    if args.delete_relation_id:
        print("Delete cloudsync relation ID: {0}".format(args.delete_relation_id))
        relation_info=netapp_api_cloud.cloudsync_delete_relations(API_TOKEN, args.account_id,args.delete_relation_id)
        if (relation_info["status"] != "success"):
                   print_deb(relation_info["status"])
                   print("ERROR: {0}".format(relation_info["message"]))

except KeyboardInterrupt:
    print ("exit")
    exit(0)