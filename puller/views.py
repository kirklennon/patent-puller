from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.urls import reverse
from django.core.exceptions import ValidationError
import json
import re

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from django.views.decorators.csrf import csrf_exempt

def new(request):
	return render(request, 'puller/new.html')

@csrf_exempt	
def search(request):
	
	searchInput = json.loads(request.body.decode('utf-8'))
	rawPatentInput = searchInput['patentNumberList']
	
	# separate and clean up patents
	patentNumberList = []
	for rawPatentNumber in rawPatentInput.splitlines():
		rawPatentNumber = rawPatentNumber.strip() 
		# Check if a patent number is valid
		# Allows the following formats, in caps and lowercase:
		# 9,123,456 RE1,1234 D999,123 (w/ or w/o commas)
		# Plus prepending US or appending A1/A2/B1/B2/E/S
		if  bool(re.match('^[USusREreDd,0-9AaBbEeSs]+$', rawPatentNumber)) is False:
			raise ValidationError('Invalid patent number')

		# Check if patent has the right amount of characters
			# implement later
		
		# craft a regex	replacement instead at some point
		barePatentNumber = rawPatentNumber.replace(',', '').replace('US', '').replace('us', '').replace('A1', '').replace('a1', '').replace('A2', '').replace('a2', '').replace('B1', '').replace('b1', '').replace('B2', '').replace('b2', '').replace('E1', '').replace('e1', '').replace('S', '').replace('s', '').replace('S1', '').replace('s1', '')
	
		patentNumberList.append(barePatentNumber)
	
	patentDictList = []
	firmNameFoundList = []
	for pn in patentNumberList:
		patentUSPTOresults = puller(pn)
		patentDictList.append(patentUSPTOresults[0])
		firmNameFoundList.append(patentUSPTOresults[1])
	
	data = {'firmNameFoundList' : firmNameFoundList}
	data['patentDictList'] = patentDictList
	return JsonResponse(data)


def puller(pn):
	
	# edit firm name here
	firmName = 'Dewey, Cheatem & Howe'.lower()
	
	patentDict = {'number' : pn}
	firmNameFoundIn = ''
	
	# pull everything but abstract, which is currently unavailable from API
	url = 'https://api.uspto.gov/api/v1/patent/applications/search'
	query = {
		"q": "applicationMetaData.patentNumber:{}".format(pn),
		"fields": [
			"applicationNumberText",
			"applicationMetaData.patentNumber",
			"applicationMetaData.inventionTitle",
			"applicationMetaData.inventorBag.inventorNameText",
			"recordAttorney","assignmentBag.correspondenceAddress", #attorneys
			"assignmentBag.conveyanceText","assignmentBag.assigneeBag.assigneeNameText","assignmentBag.assignorBag.assignorName",
			"applicationMetaData.firstApplicantName",
			"applicationMetaData.filingDate"
		],
		"pagination": {"offset": 0,"limit": 1},
		"facets": ["applicationMetaData.applicationTypeLabelName","applicationMetaData.applicationStatusCode"]
	}
	
	try:
		response = requests.post(url, json = query, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'accept': 'application/json', 'X-Api-Key': 'pnyborhldbfnjvoecdlxbtcpijctua'})
		response.raise_for_status()
		patent = response.json()["patentFileWrapperDataBag"][0]
	
	except requests.exceptions.ConnectionError:
		patentDict['title'] = "Error"
		patentDict['abstract'] = "Error"
		patentDict['inventors'] = "Error"
		originalAssignee = "Error"
	
	else:	
		patentDict['title'] = patent['applicationMetaData']['inventionTitle'].title()
		
		patentDict['abstract'] = '(N/A)'
		
		inventorList = []
		for inventorDict in patent['applicationMetaData']['inventorBag']:
			inventorList.append(inventorDict['inventorNameText'])
		patentDict['inventors'] = ', '.join(inventorList)
		
		patentDict['application'] = patent['applicationNumberText']
		
		try:		
			attorneyCurrent = patent['recordAttorney']
		except KeyError:
			pass
		else: 
			if firmName in str(attorneyCurrent).lower():
				firmNameFoundIn = '{}, '.format(pn)
		try:
			attorneyAssignmentRecords = patent['assignmentBag'] # contains correspondenceAddress for each assignment
		except KeyError:
			pass
		else:
			if firmName in str(attorneyAssignmentRecords).lower():
				firmNameFoundIn = '{}, '.format(pn)
		
		
		originalAssignee = patent['applicationMetaData']['firstApplicantName']
		
		try:
			assignmentBag = patent['assignmentBag']
			
			# find the first assignment of assignor's interest; they are always in reverse chronological order
			filteredListOfAssignments = [x for x in assignmentBag if 'ASSIGNMENT OF ASSIGNOR' in x['conveyanceText']]
			presumptiveAssignee = filteredListOfAssignments[0]['assigneeBag'][0]['assigneeNameText']
		
			# checks to see that the patent has been reassigned at least once
			if presumptiveAssignee is not None:
				finalAssignee = presumptiveAssignee
		except KeyError: # patent never reassigned; belongs to original applicant
			if originalAssignee:
				finalAssignee = originalAssignee
			else:
				finalAssignee =  '(original)'		# placeholder
		patentDict['assignee'] = finalAssignee.title().replace('Llc','LLC')
	
	return [patentDict, firmNameFoundIn]