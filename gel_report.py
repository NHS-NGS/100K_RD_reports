'''
gel_report.py
This script takes a GEL Participant ID and queries the CIP-API to return a clinical report.

This report is then modified to make it clear that this report has not been issued by GEL, including extracting some information from the local LIMS system.

Hopefully this solves a problem faced by many labs and prevents too much duplication of work!
Created 02/06/2017 by Aled Jones
'''
#from HTMLParser import HTMLParser
import requests
from bs4 import BeautifulSoup
import pdfkit
import pyodbc
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import sys
import getopt

# Import local settings
from authentication import APIAuthentication # import the function from the authentication script which generates the access token
from gel_report_config import * # config file 
from database_connection_config import * # database connection details


class connect():
	def __init__(self):
		# call function to retrieve the api token
		self.token=APIAuthentication().get_token()
	
		# The link to the first page of the CIP API results
		self.interpretationlist="https://cipapi.genomicsengland.nhs.uk/api/interpretationRequestsList/?format=json&page_size=100000"
		
		# The probandID to return the report for
		self.proband_id=""
		
		# Empty variables for report paths to be generated
		self.html_report=""
		self.pdf_report=""
		
		# A count of GeL records parsed
		self.count=0
		
		# Usage example
		self.usage = "python gel_report.py -g <GELParticipantID>"
		
		# Header line to remove
		self.old_header="Genomics England, Queen Mary University of London,"

		# Old banner colour
		self.existing_banner_css="#007C83; /*#27b7cc;*/"
		
		# new banner colour - turn header transparent so logo can be seen
		self.new_banner_css="transparent;\n    height: 100px;"
				
		# Where to add in new participant information table
		self.where_to_put_patient_info_table="<h3>Participant Information</h3>"
		
		# Where to add in new clinician info table
		self.where_to_put_clinician_info=""
		
		#line from header which states date report generated
		self.date_generated=""
		
		# variable used to move date report generated from the header into a lower table
		self.lastrow=""
		
		#variables which identify columns in the table which need changing
		self.replace_with_proband_id="Link to clinical summary"
		self.proband_id_string="GeL Proband ID"
	
	def take_inputs(self, argv):	
		'''Capture the gel participant ID from the command line'''
		# define expected inputs
		try:
			opts, args = getopt.getopt(argv, "g:")
		# raise errors with usage eg
		except getopt.GetoptError:
			print "ERROR - correct usage is", self.usage
			sys.exit(2)
		
		# loop through the arguments 
		for opt, arg in opts:
			if opt in ("-g"):
				# capture the proband ID
				self.proband_id = str(arg)
				
		if self.proband_id:
			#build paths to reports
			self.html_report=html_reports+self.proband_id+".html"
			self.pdf_report=pdf_dir+self.proband_id+".pdf"
			
			# Call the function to read the API
			self.read_API_page()
	
	def read_API_page(self):
		'''This function returns all the cases that can be viewed by the user defined by the authentication token'''
		# use requests module to return all the cases available to you
		# if proxy is set in the config file
		if proxy:
			response = requests.get(self.interpretationlist, headers={"Authorization": "JWT " + self.token},proxies=proxy) # note space is required after JWT 
		else:
			response = requests.get(self.interpretationlist, headers={"Authorization": "JWT " + self.token}) # note space is required after JWT 
		# pass this in the json format to the parse_json function
		self.parse_json(response.json())
		
			
	def parse_json(self,json):
		'''This function takes the json file containing all cases. This is parsed to look for the desired proband id'''
		# Flag to stop the search
		found=False
		
		# loop through the results
		for sample in json['results']:
			# increase the count of patients searched
			self.count += 1
			# look for the desired proband id
			if sample["proband"]==self.proband_id:
				# if sample is blocked ignore
				if sample["last_status"]=="blocked":
					print "last status = blocked for proband "+str(self.proband_id)+"\nNo Report will be generated"
					# probably want to raise an exception here
					#raise Exception("last status = blocked for proband "+str(self.proband_id))
					#quit
					quit()
				else:
					# set flag to stop the search
					found=True
										
					# create a variable to hold the various cip versions
					max_cip_ver=0

					# loop through each report to find the highest cip_version
					for j in range(len(sample["interpreted_genomes"])):
						if int(sample["interpreted_genomes"][j]["cip_version"])>max_cip_ver:
							max_cip_ver=sample["interpreted_genomes"][j]["cip_version"]

					# for the highest cip version
					for j in range(len(sample["interpreted_genomes"])):
						if sample["interpreted_genomes"][j]["cip_version"]==max_cip_ver:
							
							# take the most recent report generated for this CIP API (take the last report from the list of reports)
							#NB this SHOULD be the last in the list but the url can be edited to make 100% (https://cipapi.genomicsengland.nhs.uk/api/ClinicalReport/123/1/2/3/ - the last value (3) is the report version)
							
							# if proxy is set in the config file
							if proxy:
								report=requests.get(sample["interpreted_genomes"][j]["clinical_reports"][-1]['url'],headers={"Authorization": "JWT " + self.token},proxies=proxy)# note space is required after JWT 
							else:
								report=requests.get(sample["interpreted_genomes"][j]["clinical_reports"][-1]['url'],headers={"Authorization": "JWT " + self.token})# note space is required after JWT 

							# create an beautiful soup object for the html clinical report
							soup=BeautifulSoup(report.content,"html.parser")

							#pass the object to the replace_gel_address function and update the object
							soup=self.replace_gel_address(soup)

							#read and remove the over header (grey bar with proband id and date generated)
							soup=self.remove_over_header(soup)
							
							#pass to function to replace the GeL logo with that of the lab (and or UKAS)
							soup=self.replace_GeL_logo(soup)
							
							#pass to function to remove the banner text
							soup=self.remove_banner_text(soup)
							
							#pass to function to put things from the over header into a different table
							soup=self.move_date_report_generated(soup)

							# pass to function to expand coverage
							soup=self.expand_coverage(soup)
							
							#stop the annex tables being split over pages
							soup=self.stop_annex_tables_splitting_over_page(soup)
							
							#write html to file so can be read in edit_CSS function
							with open(self.html_report, "w") as file:
								file.write(str(soup))
							
							#Can't change CSS or insert tables using beautiful soup so need to read and replace html file
							self.edit_CSS()
							
		# if proband not found 
		if not found:
			# print statement to say not found
			print "Record not found in the "+str(self.count) + " GeL records parsed"
			# assert that the number of GEL record parsed == the sample count provided in the JSON
			assert self.count == json['count'], "self.count != gel's count"
		
	def edit_CSS(self):
		'''Can't change CSS or insert tables using beautiful soup so need to read and replace html file.
		This function reads that file, loops through it and 
		1 - edits the CSS which defines the banner colour
		2 - 
		'''
		# read file into object (a list) 
		with open(self.html_report, "r") as file:
			data=file.readlines()
		
		#loop through the file object
		for i, line in enumerate(data):
			
			## Replace the banner CSS
			# if line contains the existing banner css (from __init__)
			if self.existing_banner_css in line:
				# replace that line in the file object so it's now transparent background
				data[i]=line.replace(self.existing_banner_css,self.new_banner_css)

			## Add in the new patient info table
			# if the line is where we want to add in this table (defined in __init__)
			if self.where_to_put_patient_info_table in line:
				# open the html template
				with open(new_patientinfo_table,"r") as template:
					#write template to a list
					template_to_write=template.readlines()
				# Add in this template at this position NB this will over write the line so this line is also in the template
				data[i]="".join(template_to_write)
			
			## Add extra row to the table with the date report generated
			# if the last row of the table (as stated in the function move_date_report_generated)
			if self.lastrow in line:
				# create empty list
				template_to_write=[]
				# write the table code to the list
				template_to_write.append("<tr><td>Date Report Generated:</td><td><em>"+self.date_generated+"</em></td></tr>")
				# append the last row as below we are overwriting the existing line
				template_to_write.append(self.lastrow)
				# Add this list to the file object
				data[i]="".join(template_to_write)
			
			## Add in the clinician and address
			# look for desired location
			if self.where_to_put_clinician_info in line:
				#empty list
				template_to_write=[]
				#add new div
				template_to_write.append("<div>")
				# add line which is going to be replaced
				template_to_write.append(self.where_to_put_clinician_info)
				
				# open html template containing the clinician info structure (and a new header)
				with open(new_clinician_table,"r") as template:
					# add this file to the list
					for line in template.readlines():
						template_to_write.append(line)
				
				#write the list back to the file object
				data[i]="".join(template_to_write)
				
													
		#write the modified list back to a file
		with open(self.html_report, "w") as file:
			file.writelines(data)
						
		## Call function to pull out patient demographics from LIMS
		self.read_lims()
			
			

	def read_lims(self):
		'''This function must create a dictionary which is used to populate the html variables 
		eg patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender,"clinician":clinician,"clinician_add":clinic_address,"report_title":report_title}
		NB report_title is from the config file'''
		
		####
		# Put lab specific function to populate below dict here
		####		
		
		patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender,"clinician":clinician,"clinician_add":clinic_address,"report_title":report_title}
		#pass modified file to create a pdf.
		self.create_pdf(self.pdf_report,patient_info_dict)
			
	
	def replace_gel_address(self,html):
		'''This function looks for and removes the GeL address '''
		# notes is a list of all the p tags where the class == note
		for note in html.find_all('p', {'class':'note'}):
			# if text == gel address (as defined in the init function)
			if self.old_header in note.get_text():
				# remove the gel address tag
				note.extract()
		# return modified html
		return html
	
	def move_date_report_generated(self,html):
		'''This function looks for the table underneath the GEl address and above participant info and puts in the information from the over_header'''
		#loop through the tables - the table we are after is the only one with class=form-table and cellpadding=0
		for table in html.find_all('table', {'class':'form-table', 'cellpadding':'0'}):
			# find all rows in the table
			rows=table.find_all('tr')
			#loop through rows
			for row in rows:
				#find all columns
				cols=row.find_all('td')
				# loop through columns
				for col in cols:
					# if the column contains "Link to clinical summary"
					if self.replace_with_proband_id in col.get_text():
						# replace the string with GEL Proband ID (defined in init)
						col.string=col.get_text().replace(self.replace_with_proband_id,self.proband_id_string)
					# remove the <a> tag around the GeL ID and remove the hyperlink (link won't work without logging in first)
					for a in col.find_all('a'):
						a.replaceWithChildren()
						#delete hyperlink
						del a['href']
			#capture the last row of the table to use to insert another row to the table elsewhere in the script
			self.lastrow=str(row)
			
		#return new html							
		return html
	
	def remove_over_header(self,html):
		'''This function reads and then removes the grey bar at the top of the report containing the proband id and the date report was generated'''
		# find the span tag where class=right (should only be one - the date generated)
		for span in html.find_all('span', {'class':'right'}):
				# capture the text, and remove the Generated on string
				self.date_generated=span.get_text().replace('Generated on:','')
		
		#delete the div containing the over header 
		for div in html.find_all('div', {'class':'over-header content-div'}):
			div.decompose()
		#return new html
		return html
	
	def remove_banner_text(self,html):
		'''This function removes the title from the big green banner (Whole Genome Analysis Rare disease Primary Findings)'''
		# remove the header text
		for div in html.find_all('div', {'class':'banner-text'}):
			div.decompose()
		#return new html
		return html
	
	def stop_annex_tables_splitting_over_page(self,html):
		'''This script takes the referenced databases and software version tables and stops these being broken over pages'''
		# find all h3 tags
		for header in html.find_all('h3'):
			# Put in a page break before the referenced databases to prevent the header being on a different page to the table
			if header.get_text()=="Referenced Databases":
				# add the page break
				header['style']="page-break-before: always;"
		# find all tables
		for table in html.find_all('table'):
			#find the table head
			for head in table.find_all('thead'):
				# find each column in the header
				for col in head.find_all('th'):
					# if there is a column called name 
					if col.get_text()=="Name":
						# prevent page breaks
						table['style']=" page-break-inside: avoid !important"
		#return new html		
		return html
		
	def replace_GeL_logo(self,html):
		'''This function replaces gel logo with a new logo'''
		# find the img tag where class == logo (should only be one)
		for img in html.find_all('img', {'class':"logo"}):
			# change the src to link to new image
			img['src']=new_logo
			#change the style so is on right hand side and has a small margin
			img['style']="float:right; margin: 2%;"
			
			# capture this tag so we can use it to place the clinicians name and address
			self.where_to_put_clinician_info=str(img)
				
		return html
	



	def expand_coverage(self,html):
		'''Expand the coverage section'''
		# find the coverage div and delete so coverage seciton no longer needs to be clicked to be visible
		for section in html.find_all('div', id="coverage"):
			del(section['hidden'])

		# find the section header and remove text/hyperlink properties
		for section in html.find_all('a'):
			# find the coverage section
			if "Coverage Metrics" in section.get_text():
				# remove the extra styles no longer needed
				del(section['onclick'])
				del(section['style'])
				# create new tag and section title
				new_header="Coverage Report"
				# replace p with h3
				section.name="h3"
				# change the string
				section.string=new_header
		return html


	def create_pdf(self,pdfreport_path,patient_info):
		# add the path to wkhtmltopdf to the pdfkit config settings
		pdfkitconfig = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
		# create options to use in the footer
		options={'footer-right':'Page [page] of [toPage]','footer-left':'Date Created [isodate]','quiet':""}
		
		# use Jinja to populate the variables within the html template
		# first tell the system where to find the html template (this is written by beautiful soup above)
		env = Environment(loader=FileSystemLoader(html_reports))
		template = env.get_template(self.proband_id+".html")
		# create the pdf using template.render to populate variables from dictionary created in read_geneworks
		pdfkit.from_string(template.render(patient_info), pdfreport_path, options=options, configuration=pdfkitconfig)
		
	def fetchone(self, query):
		'''module to execute pyodbc connection. simply pass a sql query to this function and the qry result returned as an object. This function returns a single result'''
		# Connection
		cnxn = pyodbc.connect(dbconnectstring)
		# Opening a cursor
		cursor = cnxn.cursor()
		#perform query
		cursor.execute(query)
		#capture result
		result = cursor.fetchone()
		#yield result
		if result:
			return result
			#for i in result:
			#	print i
				#yield(result)
		else:
			print "no result found"
	
	def fetchall(self, query):
		'''module to execute pyodbc connection. simply pass a sql query to this function and the qry result returned as an object. This function returns all results'''
		# Connection
		cnxn = pyodbc.connect(dbconnectstring)
		# Opening a cursor
		cursor = cnxn.cursor()
		#perform query
		cursor.execute(query)
		#capture result
		result = cursor.fetchall()
		#yield result
		if result:
			return(result)
		else:
			print "no result found"
		
if __name__=="__main__":
	c=connect()
	c.take_inputs(sys.argv[1:])
