from django import forms
from django.core.exceptions import ValidationError
import re

class PatentForm(forms.Form):
	patents = forms.CharField(widget=forms.Textarea(attrs={"rows":10, "cols":20}), label='Patent Numbers', help_text='Enter a patent number on each line')
	
	def clean_patents(self):
		rawPatentInput = self.cleaned_data['patents']
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
			barePatentNumber = rawPatentNumber.replace(',', '').replace('US', '').replace('us', '').replace('A1', '').replace('a1', '').replace('A2', '').replace('a2', '').replace('B1', '').replace('b1', '').replace('B2', '').replace('b2', '').replace('E', '').replace('e', '').replace('E1', '').replace('e1', '').replace('S', '').replace('s', '').replace('S1', '').replace('s1', '')
		
			patentNumberList.append(barePatentNumber)
		# new list
		return patentNumberList