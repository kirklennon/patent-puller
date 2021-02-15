from django import forms
from django.core.exceptions import ValidationError
import re

class PatentForm(forms.Form):
	patents = forms.CharField(max_length = 100, help_text='Enter a patent number')
	
	def clean_patents(self):
		data = self.cleaned_data['patents']

		# Check if a patent number is valid
		# Allows the following formats, in caps and lowercase:
		# 9,123,456 RE1,1234 D999,123 (w/ or w/o commas)
		# Plus prepending US or appending A1/A2/B1/B2
		if  bool(re.match('^[USusREreDd,0-9AaBb]+$', data)) is False:
			raise ValidationError('Invalid patent number')

		# Check if patent has the right amount of characters
			# implement later

		return data