from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse

from puller.forms import PatentForm

import requests
import xml.etree.ElementTree as ET
import concurrent.futures

def namelister(inventorsRaw):
	'''Combines all inventors into a    
	single comma-separated list'
	'''
	inventorList = []
	for inventor in inventorsRaw:
		inventorList.append(inventor["inventor_first_name"] + ' ' + inventor["inventor_last_name"])
	if len(inventorList) == 1:
		return inventorList[0]
	else:
		return ', '.join(inventorList) 



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
	url = f'https://api.patentsview.org/patents/query?q=\u007b"patent_number":"{pn}"\u007d&f=["patent_title","patent_abstract","assignee_organization","lawyer_organization","patent_number","inventor_first_name","inventor_last_name"]'
	
	patent = requests.get(url, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36', 'accept': 'application/json'}).json()["patents"][0]
	
	patentDict['title'] = patent["patent_title"]
	
	if patent["patent_abstract"] is not None:
		patentDict['abstract'] = patent["patent_abstract"]
	else:
		patentDict['abstract'] = '(none)'
	
	inventorsRaw = patent["inventors"]
	patentDict['inventors'] = namelister(inventorsRaw)
	
	lawFirm = patent["lawyers"][0]["lawyer_organization"]
	
	originalAssignee = patent["assignees"][0]["assignee_organization"]
	

	# pull reassignment information
	url = 'https://assignment-api.uspto.gov/patent/lookup?query={}&filter=PatentNumber&fields=main'.format(pn)
	rawXML = requests.get(url).text
	
	# Check if firm worked on patent previously
	firmName = 'NameOfFirm'
	firmNameFoundIn = ''
	
	if lawFirm is not None:
		if firmName in lawFirm:
			firmNameFoundIn = str(pn)
		
	if firmName.upper() in rawXML:
		firmNameFoundIn = str(pn)
	
	tree = ET.fromstring(rawXML)
	presumptiveAssignee = tree.findtext(".//*[str='ASSIGNMENT OF ASSIGNORS INTEREST (SEE DOCUMENT FOR DETAILS).']/*[@name='patAssigneeName']/str")
	# finds first patAssigneeName that's a sibling of an assignment of 
	# assignor's interest. This skips security interest assignments.
	if presumptiveAssignee is not None:
	# checks to see that the patent has been reassigned at least once
		nameChangeAssignee = tree.findtext(".//*[str='CHANGE OF NAME (SEE DOCUMENT FOR DETAILS).']/*[@name='patAssigneeName']/str")
		nameChangeAssignor = tree.findtext(".//*[str='CHANGE OF NAME (SEE DOCUMENT FOR DETAILS).']/*[@name='patAssignorName']/str")
		if nameChangeAssignee is not None:
		# Checks to see if any assignee changed its name
			if nameChangeAssignor.split(' ')[0] == presumptiveAssignee.split(' ')[0]:
			# A previous assignee may have changed its name and then reassigned 
			# so this checks to make sure the name change is for the presumptive
			# assignee. Sometimes there are slight discrepancies in the name   
			# so it compares only the first word. Still doesn't catch this edge case:
			# Initial Inc. renamed Initial LLC reassigns to Final Inc.
				finalAssignee = nameChangeAssignee
			else:
				# somebody changed names but it wasn't the presumptive assignee
				finalAssignee = presumptiveAssignee
		else:
			# nobody changed names
			finalAssignee = presumptiveAssignee
	else: # patent never reassigned; belongs to original applicant
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