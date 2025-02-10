from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.urls import reverse
from django.core.exceptions import ValidationError
import json
import re

from puller.forms import PatentForm

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from django.views.decorators.csrf import csrf_exempt

import xml.etree.ElementTree as ET
import concurrent.futures

def namelister(inventorsRaw):
	'''Combines all inventors into a    
	single comma-separated list'
	'''
	inventorList = []
	for inventor in inventorsRaw:
		inventorList.append(inventor["inventor_name_first"] + ' ' + inventor["inventor_name_last"])
	if len(inventorList) == 1:
		return inventorList[0]
	else:
		return ', '.join(inventorList) 

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

def index(request):
	return HttpResponse("Hello, world.")
	
def form_view(request_iter):
	form = Patentform()

	if request_iter.method == "POST":
		value = Patentform(request_iter.POST)
	return  render(request_iter,'form_handling.html', {"form": form})
	

def puller(pn):
	patentDict = {'number' : pn}
	# pull everything but assignee
	url = 'https://search.patentsview.org/api/v1/patent/'
	query = {
		  "f": ["patent_title","patent_abstract","patent_id", "attorneys.attorney_organization", "application.application_id", "inventors.inventor_name_first", "inventors.inventor_name_last", "assignees.assignee_organization"],
		  "q": { "patent_id": pn}
		}
	
	try:
		patent = requests.post(url, json = query, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'accept': 'application/json', 'X-Api-Key': 'InsertPatentsViewAPIKeyHere'})
		patent.raise_for_status()
		patent = patent.json()["patents"][0]
	
	except requests.exceptions.ConnectionError:
		patentDict['title'] = "Error"
		patentDict['abstract'] = "Error"
		patentDict['inventors'] = "Error"
		lawFirm = None
		originalAssignee = "Error"
	
	else:	
		patentDict['title'] = patent["patent_title"]
		
		if patent["patent_abstract"] is not None:
			patentDict['abstract'] = patent["patent_abstract"]
		else:
			patentDict['abstract'] = '(none)'
		
		inventorsRaw = patent["inventors"]
		patentDict['inventors'] = namelister(inventorsRaw)
		
		lawFirm = patent["attorneys"][0]["attorney_organization"]
		
		originalAssignee = patent["assignees"][0]["assignee_organization"]
	

	# pull reassignment information
	url = 'https://beta-api.uspto.gov/api/v1/patent/applications/{}/assignment'.format(patent["application"][0]["application_id"].replace('/',''))
	
	# Check if firm worked on patent previously
	firmName = 'Firm Name Goes Here'
	firmNameFoundIn = ''
	
	try:
		response = requests.get(url, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'accept': 'application/json', 'X-API-KEY': 'InsertUSPTOOpenDataPortalAPIKeyHere'})
		response.raise_for_status()
		
	except requests.exceptions.ConnectionError:
		patentDict['assignee'] = "Error"
		
	else:	
		if lawFirm is not None:
			if firmName in lawFirm:
				firmNameFoundIn = str(pn)
				
		if firmName.upper() in response.text:
			firmNameFoundIn = str(pn)
		
		response = response.json()
		
		# check to see if there is any reassignment data
		try:
			assignmentBag = response["patentFileWrapperDataBag"][0]["assignmentBag"]
			
			# find the first assignment of assignor's interest; they are always in reverse chronological order
			filteredListOfAssignments = [x for x in assignmentBag if x["conveyanceText"]=="ASSIGNMENT OF ASSIGNORS INTEREST (SEE DOCUMENT FOR DETAILS)."]
			presumptiveAssignee = filteredListOfAssignments[0]["assigneeBag"][0]["assigneeNameText"]
		
			# checks to see that the patent has been reassigned at least once
			if presumptiveAssignee is not None:
			
			
			
				# Below block searched for name changes using the old XML API. It needs to be re-implemented using
				# the new JSON API. Leaving this code here for the overall logic and relevant strings
				
				# nameChangeAssignee = tree.findtext(".//*[str='CHANGE OF NAME (SEE DOCUMENT FOR DETAILS).']/*[@name='patAssigneeName']/str")
				# nameChangeAssignor = tree.findtext(".//*[str='CHANGE OF NAME (SEE DOCUMENT FOR DETAILS).']/*[@name='patAssignorName']/str")
				# if nameChangeAssignee is not None:
				# # Checks to see if any assignee changed its name
				# 	if nameChangeAssignor.split(' ')[0] == presumptiveAssignee.split(' ')[0]:
				# 	# A previous assignee may have changed its name and then reassigned 
				# 	# so this checks to make sure the name change is for the presumptive
				# 	# assignee. Sometimes there are slight discrepancies in the name   
				# 	# so it compares only the first word. Still doesn't catch this edge case:
				# 	# Initial Inc. renamed Initial LLC reassigns to Final Inc.
				# 		finalAssignee = nameChangeAssignee
				# 	else:
				# 		# somebody changed names but it wasn't the presumptive assignee
				# 		finalAssignee = presumptiveAssignee
				# else:
				# 	# nobody changed names
					finalAssignee = presumptiveAssignee
		except KeyError: # patent never reassigned; belongs to original applicant
			if originalAssignee:
				finalAssignee = originalAssignee
			else:
				finalAssignee =  '(original)'		# placeholder
		patentDict['assignee'] = finalAssignee.title().replace('Llc','LLC')
	return [patentDict, firmNameFoundIn]
def patent_form(request):

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = PatentForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			
			patentDictList = []
			firmNameFoundList = []
			
			patentNumberList = form.cleaned_data['patents']
			
			with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
				future_to_patent = {executor.submit(puller, pn): pn for pn in patentNumberList}
				for future in concurrent.futures.as_completed(future_to_patent):
					patentDictList.append(future.result()[0])
					firmNameFoundList.append(future.result()[1])

			context = {
				'patentDictList' : patentDictList,
				'firmNameFoundList': firmNameFoundList,
			}
			
			return render(request, 'puller/patent_results.html', context)

	# If this is a GET (or any other method) create the default form.
	else:
		form = PatentForm()

	context = {
		'form': form,
	}

	return render(request, 'puller/patent_form.html', context)