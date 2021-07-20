#!/usr/bin/python
#Author: Sidharth.Mohapatra@Honeywell.com
#Description: This is the automation for creating Patching Schedule
#DT: 25.10.2020

import http.client
import mimetypes
import json
import uuid
from optparse import OptionParser 
import sys
import argparse,datetime
from datetime import datetime



#Take Inputs
parser = OptionParser(usage='usage: %prog [options] arguments')
parser.add_option('--rg',help="Azure Resource Group",action="store", dest="resourceGroup")
parser.add_option('--sn',help="Azure Subscription Name",action="store", dest="subName")
parser.add_option('--pd',help="Patching Date: Ex 2020-12-12",action="store", dest="patchDate")
parser.add_option('--pt',help="Patching Start Time: Ex 10:30",action="store", dest="startTime")


   
#Create a token
def createToken():
	conn = http.client.HTTPSConnection("login.microsoftonline.com")
	payload = 'grant_type=client_credentials&client_id=6ea87740-03ac-4c0f-823f-be4f42df7b5c&client_secret=ySQ9Q.soS.4WbTXvm%7E_4O%7E_019I28OUQ41&resource=https%3A//management.azure.com/&directoryid=96ece526-9c7d-48b0-8daf-8b93c90a5d18'
	headers = {
  		'Content-Type': 'application/x-www-form-urlencoded',
  		'Cookie': 'x-ms-gateway-slice=prod; stsservicecookie=ests; fpc=AiNVmTmG7fNChenld3k9v87g-hOIAgAAALBKKNcOAAAA; esctx=AQABAAAAAAB2UyzwtQEKR7-rWbgdcBZIhFu4bH8FAK7hQvAcDt3vksvtHPlzC5Rtm05blwyN7yfM4WAbQTm7_ncnGOJIwA6y4AccCy_7gf5CI6-FI6iu9yeSzzqAskPKmKL4lrJKSDzBNnVPYvApJeUJ2z_n3l1JbYyI-KV2MeIfI6_4BVPAtAoTBBS2XgrpdnQiD9_lBYEgAA; x-ms-gateway-slice=prod; stsservicecookie=ests; fpc=AtT4jOX69PxIt3MMnLQUOsLg-hOIAgAAAGxLKNcOAAAA'
	}
	conn.request("POST", "/96ece526-9c7d-48b0-8daf-8b93c90a5d18/oauth2/token", payload, headers)
	res = conn.getresponse()
	data = res.read()
	token=json.loads(data.decode("utf-8"))
	accessToken=(token['access_token'])
	return accessToken


#Create a schedule
def createSchedule(accessToken,patchingTime,scheduleName):
	#2020-10-28T10:30:00+05:30 -- time reference
	conn = http.client.HTTPSConnection("management.azure.com")
	payload = "{\n  \"name\": \""+scheduleName+"\",\n  \"properties\": {\n    \"description\": \"my description of schedule goes here\",\n    \"startTime\": \""+patchingTime+"\",\n    \"frequency\": \"OneTime\",\n    \"timeZone\": \"India Standard Time\"   \n  }\n}"
	headers = {
  	'Content-Type': 'application/json',
  	'Authorization': 'Bearer '+accessToken+'' 
	}
	conn.request("PUT", "/subscriptions/f365c4f8-69b0-4f28-bd9b-ca885182bad6/resourceGroups/DPS-CSA-Security-Engineering-RG/providers/Microsoft.Automation/automationAccounts/Hon-Central-LA-Prod/schedules/"+scheduleName+"?api-version=2015-10-31", payload, headers)
	res = conn.getresponse()
	data = res.read()
	print(data.decode("utf-8"))


#Link the schedule
#scheduleName='sid-test'
#runBookName='sid-test'
def linkSchedule(scheduleName,runBookName):
	conn = http.client.HTTPSConnection("management.azure.com")
	payload = "{\n  \"properties\": {\n    \"schedule\": {\n      \"name\": \""+scheduleName+"\"\n    },\n    \"runbook\": {\n      \"name\": \""+runBookName+"\"\n    }\n  }\n}"
	uuidToken=uuid.uuid1()
	headers = {
  	'Content-Type': 'application/json',
  	'Authorization': 'Bearer '+accessToken+''}
	conn.request("PUT", "/subscriptions/f365c4f8-69b0-4f28-bd9b-ca885182bad6/resourceGroups/DPS-CSA-Security-Engineering-RG/providers/Microsoft.Automation/automationAccounts/Hon-Central-LA-Prod/jobSchedules/"+str(uuidToken)+"?api-version=2015-10-31", payload, headers)
	res = conn.getresponse()
	data = res.read()
	print(data.decode("utf-8"))

def checkSubName():
	key = options.subName
	val = options.resourceGroup
	if key in subNames.keys():
		if val == subNames[key]:
			print "\nSubscription Name and Resource Group Name are matching !!"
			if val in runBooks.keys():
				runBookName = runBooks[val]
				return runBookName
		else:
			print "\nSubscription Name and Resource Group Name are not matching !!\n"
			print "Please check the below list and re-run again"
			print "\nSubscription Name:Resource Group Name"
			for x,y in subNames.items():
				print x+":" + y
			sys.exit(-1)
	else:
		print "\nSubscription Name not present"
		print "Please check the below list and re-run again"
		print "\nSubscription Name:Resource Group Name"
		for x,y in subNames.items():
			print x+":" + y
		sys.exit(-1)

def validateTime():
	i = str(options.patchDate+' '+options.startTime)
	try:
    		dt_start_tmp = datetime.strptime(i, '%Y-%m-%d %H:%M')
		dt_start=datetime.strftime(dt_start_tmp,'%Y-%m-%d %H:%M')
		dt_now = datetime.today().strftime('%Y-%m-%d %H:%M')
		if dt_start < dt_now:
			print "Patching date cannot be less than the current date"
			return False
		return True
	except ValueError:
    		print "Date/Time is in incorrect format, see help using -h or --help"

if( __name__ == '__main__'):
	global runBookName
	(options, args) = parser.parse_args()

	if options.resourceGroup is None or options.subName is None or options.patchDate is None or options.startTime is None:
        	parser.error('Not all arguments passed:See -h or --help')
		sys.exit(-1)

	runBooks = {'sid-test':'sid-test','IMSQA-USE-RG':'UM-HCE-CHQ-QForgeIOTPlatform-NonProd-IMSQA','IMSPROD-USE-RG':'UM-SPS-ForgeIMS-Prod','dev-spec-eastus':'UM-HCE-CHQ-AppHosting-NonProd-dev-39-ocp','spec-prod-eastus':'UM-HCE-CHQ-AppHosting-Prod-prod-39-ocp','HCE-Apphosting-EU':'UM-HCE-CHQ-NonProd-dev-311-ocp','HCE-AppHosting-EU-Prod':'UM-HCE-CHQ-Prod-prod-311-ocp','SENTFASTDBLOADENTGROUP':'UM-HCE-CHQ-ForgeIOT-NonProd-SendFast','sentfastdbqaentgroup':'UM-HCE-CHQ-QForgeIOTPlatform-NonProd-Sentfast','sentfastdb01eusprodentgroup':'UM-HCE-CHQ-ForgeGraphDB-Prod-SendFast'}
	
	subNames = {'sid-test':'sid-test','HCE-CHQ-QConnectedBuildings-NonProd':'IMSQA-USE-RG','SPS-ForgeIMS-Prod':'IMSPROD-USE-RG','HCE-CHQ-AppHosting-NonProd':'dev-spec-eastus','HCE-CHQ-AppHosting-Prod':'spec-prod-eastus','HCE-CHQ-NonProd':'HCE-Apphosting-EU','HCE-CHQ-Prod':'HCE-AppHosting-EU-Prod','HCE-CHQ-ForgeIOT-NonProd':'SENTFASTDBLOADENTGROUP','HCE-CHQ-QForgeIOTPlatform-NonProd':'sentfastdbqaentgroup','HCE-CHQ-ForgeGraphDB-Prod':'sentfastdb01eusprodentgroup'}
	
	
	if validateTime() is True:
		runBookName=checkSubName()
		patchingTime=options.patchDate+'T'+options.startTime+':00+05:30'
		#print patchingTime
		accessToken=createToken()
		createSchedule(accessToken,patchingTime,options.subName+'-schedule')
		linkSchedule(options.subName+'-schedule',runBookName)
