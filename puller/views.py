from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse

from puller.forms import PatentForm

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import concurrent.futures

def nameflipper(raw):
	'''Takes name in the format 'Doe; John A.'   
	and returns it as 'John A. Doe'
	'''
	splitname = raw.split(';')
	return splitname[1].lstrip() + ' ' + splitname[0]
	
def namelister(inventorsraw):
	'''Combines all inventors into a    
	single comma-separated list'
	'''
	inventorlist = []
	for inventor in inventorsraw:
		if inventor.text.startswith(','):
			inventorlist.append(nameflipper(inventor.text[2:]))
		elif len(inventor.text) == 2:	
		#country code for international inventors is bolded; need to skip
			pass
		else: 
			inventorlist.append(nameflipper(inventor.text))
	
	if len(inventorlist) == 1:
		return inventorlist[0]
	else:
		return ', '.join(inventorlist) 



def index(request):
	return HttpResponse("Hello, world.")
	
def form_view(request_iter):
	form = Patentform()

	if request_iter.method == "POST":
		value = Patentform(request_iter.POST)
	return  render(request_iter,'form_handling.html', {"form": form})
	

def puller(pn):
	patentDict = {'number' : pn}
	# scrape everything but assignee
	url = 'http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1={}.PN.&OS=PN/{}&RS=PN/{}'.format(pn,pn,pn)

	request_header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
	page = requests.get(url, headers=request_header).text

	soup = BeautifulSoup(page, 'html.parser')
	
	patentDict['title'] = soup.find("font", {"size": "+1"}).text
	
	inventorcolumn = soup.find("th").parent.td
	inventorsraw = inventorcolumn.find_all('b')
	patentDict['inventors'] = namelister(inventorsraw)
	patentDict['abstract'] = soup.find('p').text

	# pull assignment information
	url = 'https://assignment-api.uspto.gov/patent/lookup?query={}&filter=PatentNumber&fields=main'.format(pn)
	tree = ET.fromstring(requests.get(url).text)
	patentDict['assignee'] = tree.findtext(".//*[@name='patAssigneeName']/str").title()
	return patentDict
def patent_form(request):

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = PatentForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			
			patentDictList = []
			
			patentNumberList = form.cleaned_data['patents']
			
			with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
				future_to_patent = {executor.submit(puller, pn): pn for pn in patentNumberList}
				for future in concurrent.futures.as_completed(future_to_patent):
					patentDictList.append(future.result())

			context = {
				'patentDictList' : patentDictList,
			}
			
			return render(request, 'puller/patent_results.html', context)

	# If this is a GET (or any other method) create the default form.
	else:
		form = PatentForm()

	context = {
		'form': form,
	}

	return render(request, 'puller/patent_form.html', context)