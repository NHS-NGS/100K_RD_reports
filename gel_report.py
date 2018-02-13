'''
gel_report.py
This script takes a GEL Participant ID and queries the CIP-API to return a clinical report.

This report is then modified to make it clear that this report has not been issued by GEL, including extracting some information from the local LIMS system.

Hopefully this solves a problem faced by many labs and prevents too much duplication of work!
Created 02/06/2017 by Aled Jones
'''
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
import gel_report_config as config # config file 
from database_connection_config import * # database connection details
import GEL_logo as gel_logo


class connect():
	def __init__(self):
		# call function to retrieve the api token
		self.token=APIAuthentication().get_token()
	
		# The link to the first page of the CIP API results
		self.interpretationlist = "https://cipapi.genomicsengland.nhs.uk/api/2/interpretation-request?cip={cip}&status=sent_to_gmcs%2Creport_generated%2Creport_sent&members={proband}&format=json"
		
		# The probandID to return the report for
		self.proband_id = ""
		
		# Empty variables for report paths to be generated
		self.html_report = ""
		self.pdf_report = ""
		
		# Usage example
		self.usage = "python gel_report.py -g <GELParticipantID> -h True/False"
		
		# Header line to remove
		self.old_header = "Genomics England, Queen Mary University of London,"

		# Old banner colour
		self.existing_banner_css = "#007C83; /*#27b7cc;*/"
		
		# new banner colour - turn header transparent so logo can be seen
		self.new_banner_css = "transparent;\n    height: 100px;"
				
		# Where to add in new participant information table
		self.where_to_put_patient_info_table = "<h3>Participant Information</h3>"
		
		# Where to add in new clinician info table
		self.where_to_put_clinician_info = ""
		
		#line from header which states date report generated
		self.date_generated = ""
		
		# variable used to move date report generated from the header into a lower table
		self.lastrow = ""
		
		#variables which identify columns in the table which need changing
		self.replace_with_proband_id = "Link to clinical summary"
		self.proband_id_string = "GeL Proband ID"
		
		# a flag to determine if the header is required to be changed to look like a report from the lab (as opposed to keeping the Gel geader to make it clear it's a GEL report).
		self.remove_headers = ""
		
		# create a variable to hold the various cip versions
		self.max_cip_ver = 0
	
	def take_inputs(self, argv):	
		'''Capture the gel participant ID from the command line'''
		# define expected inputs
		try:
			opts, args = getopt.getopt(argv, "g:h:", ['gelid', 'removeheader'])
		# raise errors with usage eg
		except getopt.GetoptError:
			print "ERROR - correct usage is", self.usage
			sys.exit(2)
		
		# loop through the arguments 
		for opt, arg in opts:
			if opt in ("-g", "--gelid"):
				# capture the proband ID
				self.proband_id = str(arg)
			
			if opt in ("-h", "--removeheader"):
				# If this flag is given don't touch the report header.
				self.remove_headers = str(arg)
				
		if self.proband_id:
			#build paths to reports
			self.htmlfilename = self.proband_id + ".html"
			self.html_report = config.html_reports + self.htmlfilename
			self.pdf_report = config.pdf_dir + self.proband_id + ".pdf"
			
			
	
			# Call the function to read the API
			json = self.read_API_page()
			# if test passed parse the json to pull out report
			self.parse_json(json)
	
	def read_API_page(self):
		'''
		This function uses the authentication token to read the interpretation request list end point
		This endpoint is filtered based on the CIP, status and the proband ID
		The resulting json is returned
		'''
		# use requests module to return all the cases available to you
		
		# insert CIP and proband into url
		self.interpretationlist = self.interpretationlist.format(cip = config.CIP, proband = self.proband_id)
		# if proxy is set in the config file
		if config.proxy:
			response = requests.get(self.interpretationlist, headers = {"Authorization": "JWT " + self.token}, proxies = config.proxy) # note space is required after JWT 
		else:
			response = requests.get(self.interpretationlist, headers = {"Authorization": "JWT " + self.token}) # note space is required after JWT 
		# pass this in the json format to the parse_json function
		return response.json()
		
			
	def parse_json(self,json):
		'''
		This function takes the json file containing all cases whcih match the CIP, status and proband filter. 
		A few checks are performed to ensure there is only one record before the record is parsed and the report is downloaded and modified
		'''	
		# loop through the results
		if json['count'] == 0:
			print "no record for proband %s with the status sent_to_gmcs,report_generated or report_sent" % (self.proband_id)
		elif json['count'] > 1:
			print "STOP - multiple unblocked interpretation requests for desired CIP (%s) found for proband %s\nPlease inform GEL" % (config.CIP, self.proband_id)
		else:
			for sample in json['results']:
				# ensure have found the desired proband id and make sure correct CIP
				assert sample["proband"] == self.proband_id and sample["cip"] == config.CIP
				
				# variable to record the highest version of the report
				highest_report_version = 0
				# variable to record URL for the html report
				highest_report_url = ""

				# loop through each report in the clinical_reports section to get the highest report version
				for report_number in range(len(sample["clinical_reports"])):
					# capture the verison number from the report url - it's the last number eg the last value (3) in the link https://cipapi.genomicsengland.nhs.uk/api/ClinicalReport/123/1/2/3
					report_version_number = sample["clinical_reports"][report_number]["url"].split("/")[-1]
					# if this is the highest report number
					if report_version_number > highest_report_version:
						# capture the new highest report version and url
						highest_report_version = report_version_number
						highest_report_url = sample["clinical_reports"][report_number]["url"]


				# loop through each interpreted genome to find the highest cip_version
				for interpreted_genome in range(len(sample["interpreted_genomes"])):
					if int(sample["interpreted_genomes"][interpreted_genome]["cip_version"]) > self.max_cip_ver:
						self.max_cip_ver = sample["interpreted_genomes"][interpreted_genome]["cip_version"]
				
				#read the interpretation_request to pull out any variants
				self.read_interpretation_request(sample)

				# if proxy is set in the config file
				if config.proxy:
					report = requests.get(highest_report_url, headers = {"Authorization": "JWT " + self.token}, proxies = config.proxy)# note space is required after JWT 
				else:
					report = requests.get(highest_report_url, headers = {"Authorization": "JWT " + self.token})# note space is required after JWT 

				# create an beautiful soup object for the html clinical report
				soup = BeautifulSoup(report.content, "html.parser")
				
				#check for errors first
				soup = self.check_for_errors(soup)
				
				# if headers are to be removed (not a negative negative)
				if self.remove_headers == "True":
					
					#pass the object to the replace_gel_address function and update the object
					soup = self.replace_gel_address(soup)

					#read and remove the over header (grey bar with proband id and date generated)
					soup = self.remove_over_header(soup)
													
					#pass to function to remove the banner text
					soup = self.remove_banner_text(soup)
					
					#pass to function to put things from the over header into a different table
					soup = self.move_date_report_generated(soup)
					
					
				#pass to function to replace the GeL logo with that of the lab (and or UKAS)
				soup = self.replace_GeL_logo(soup)
				
				#stop the annex tables being split over pages
				soup = self.stop_annex_tables_splitting_over_page(soup)
				
				# pass to function to expand coverage
				soup = self.expand_coverage(soup)
											
				#write html to file so can be read in edit_CSS function
				with open(self.html_report, "w") as file:
					file.write(str(soup))

				## Call function to pull out patient demographics from LIMS. capture dict
				patient_info_dict = self.read_lims(sample["sites"])
				
				#Can't change CSS or insert tables using beautiful soup so need to read and replace html file
				self.edit_CSS(patient_info_dict)
				
				print "creating clinical report"
				
				#pass modified file to create a pdf.
				self.create_pdf(self.htmlfilename, self.pdf_report, patient_info_dict)


					
	def edit_CSS(self,patient_info_dict):
		'''Can't change CSS or insert tables using beautiful soup so need to read and replace html file.
		This function reads that file, loops through it and 
		1 - Adds in a table containing patient information extracted from LIMS
		
		for reports that are being modified to look like they are not from gel:
			2 - edits the CSS which defines the banner colour so it is transparent
			3 - Adds the date report generated to the table (was previously in the grey header)
			4 - Adds in table with clinician referral information			
		'''
		# read file into object (a list) 
		with open(self.html_report, "r") as file:
			data = file.readlines()
			#loop through the file object
			for i, line in enumerate(data):
				## Add in the new patient info table
				# if the line is where we want to add in this table (defined in __init__)
				if self.where_to_put_patient_info_table in line:
					# open the html template
					with open(config.new_patientinfo_table,"r") as template:
						#write template to a list
						template_to_write = template.readlines()
						# Add in this template at this position NB this will over write the line so this line is also in the template
						data[i] = "".join(template_to_write)
				
				# if it's a report which is to be modified
				if self.remove_headers == "True":
					## Replace the banner CSS
					# if line contains the existing banner css (from __init__)
					if self.existing_banner_css in line:
						# replace that line in the file object so it's now transparent background
						data[i]=line.replace(self.existing_banner_css, self.new_banner_css)
				
					## Add extra row to the table with the date report generated
					# if the last row of the table (as stated in the function move_date_report_generated)
					if self.lastrow in line:
						# create empty list
						template_to_write = []
						# write the table code to the list
						template_to_write.append("<tr><td>Date Report Generated:</td><td><em>" + self.date_generated + "</em></td></tr>")
						# append the last row as below we are overwriting the existing line
						template_to_write.append(self.lastrow)
						# Add this list to the file object
						data[i] = "".join(template_to_write)
					
					## Add in the clinician and address
					# look for desired location
					if self.where_to_put_clinician_info in line:
						#empty list
						template_to_write = []
						#add new div
						#template_to_write.append("<div>")
						# add line which is going to be replaced
						template_to_write.append(self.where_to_put_clinician_info)
						
						# open html template containing the clinician info structure (and a new header)
						with open(config.new_clinician_table,"r") as template:
							# add this file to the list
							for line in template.readlines():
								#print patient_info_dict['clinician1']									
								if line.startswith("<p>cc.{{copies}}</p>"):
									if patient_info_dict['copies'] == "":
										pass
									else:
										template_to_write.append(line)
								else:
									template_to_write.append(line)
								
						# add the new html code back to the list
						data[i] = "".join(template_to_write)
				
				# otherwise add in clinician info for less heavily modified reports
				else:		
					## Add in the clinician and address
					# look for desired location
					if gel_logo.gel_logo_code in line:
						#empty list
						template_to_write = []
						# add line which is going to be replaced
						template_to_write.append(gel_logo.gel_logo_code)
						
						# open html template containing the clinician info structure (and a new header)
						with open(config.new_clinician_table,"r") as template:
							# add this file to the list
							for line in template.readlines():
								#print patient_info_dict['clinician1']									
								if line.startswith("<p>cc.{{copies}}</p>"):
									if patient_info_dict['copies'] == "":
										pass
									else:
										template_to_write.append(line)
								else:
									template_to_write.append(line)
										
						# add the new html code back to the list
						data[i] = "".join(template_to_write)

			#write the modified list back to a file
			with open(self.html_report, "w") as file:
				file.writelines(data)
	

	def read_lims(self, sites):
		'''This function must create a dictionary which is used to populate the html variables 
		eg patient_info_dict={"NHS":NHS,"InternalPatientID":InternalPatientID,"dob":DOB,"firstname":FName,"lastname":LName,"Sex":Sex,"clinician1":clinician1,"clinician1_add":clinician1_address,"copies":copies,"report_title":report_title}
		NB report_title is from the config file'''
		
		# TO BE COMPLETED BY EACH GMC
		if find_patient:
			# complete the dictionary
			patient_info_dict={"NHS":NHS,"InternalPatientID":InternalPatientID,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender,"clinician":clinician,"clinician_add":clinic_address,"report_title":report_title}
			
			#return the dictionary
			return patient_info_dict
		else:
			# report error and quit if can't find all the required info (or if it doesn't meet required formats)
			print "No Patient information for that proband in database\ncannot create report"
			quit()
		
	
	
	def check_for_errors(self, html):
		'''issue warning (or abort) if any errors are found when reporting eg can't find coverage report etc. Uses a warning message from config file'''
		# look for presence of an warning message
		for div in html.find_all('div', {'class':'content-div error-panel'}):
			# if there is an error
			if div:
				# capture and print the error message
				for message in div.find_all('p'):
					print (config.warning_message % self.proband_id) + message.get_text()
				
				#if required stop the report being generated
				#quit()
				
		# return html
		return html
			
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
		
		# find all tables
		for table in html.find_all('table'):
			#find the table head
			for head in table.find_all('thead'):
				# find each column in the header
				for col in head.find_all('th'):
					# if there is a column called name 
					if col.get_text() == "Name":
						# prevent page breaks
						table['style'] = " page-break-inside: avoid !important"
		#return new html		
		return html
		
	def replace_GeL_logo(self,html):
		'''This function replaces gel logo with a new logo'''
		if self.remove_headers == "True":
			# find the img tag where class == logo (should only be one)
			for img in html.find_all('img', {'class':"logo"}):
				# change the src to link to new image
				img['src'] = config.new_logo
				#change the style so is on right hand side and has a small margin
				img['style'] = "float:right; margin: 2%;"
				
				# capture this tag so we can use it to place the clinicians name and address
				self.where_to_put_clinician_info = str(img)
		else:
			# find the img tag where class == logo (should only be one)
			for img in html.find_all('img', {'class':"logo"}):
				# Need to ensure the image doesn't shrink
				img['style'] = "height:100px;"
		
		# return the modified html
		return html
	
	def expand_coverage(self,html):
		'''Expand the coverage section'''
		# find the coverage div and delete so coverage seciton no longer needs to be clicked to be visible
		for section in html.find_all('div', id = "coverage"):
			del(section['hidden'])

		# find the section header and remove text/hyperlink properties
		for section in html.find_all('a'):
			# find the coverage section
			if "Coverage Metrics" in section.get_text():
				# remove the extra styles no longer needed
				del(section['onclick'])
				del(section['style'])
				# create new tag and section title
				new_header = "Coverage Report"
				# replace p with h3
				section.name = "h3"
				# change the string
				section.string = new_header
		return html


	def create_pdf(self, htmlfilename, pdfreport_path, patient_info):
		# add the path to wkhtmltopdf to the pdfkit config settings
		pdfkitconfig = pdfkit.configuration(wkhtmltopdf=config.wkhtmltopdf_path)
		# create options to use in the footer
		options = {'footer-right':'Page [page] of [toPage]','footer-left':'Date Created [isodate]','quiet':""}
				
		# use Jinja to populate the variables within the html template
		# first tell the system where to find the html template (this is written by beautiful soup above)
		env = Environment(loader=FileSystemLoader(config.html_reports))
		template = env.get_template(htmlfilename)
		
		# create the pdf using template.render to populate variables from dictionary created in read_geneworks
		pdfkit.from_string(template.render(patient_info), pdfreport_path, options=options, configuration=pdfkitconfig)
		
		# print 
		print "Report can be found at "+pdfreport_path
		
	def fetchone(self, query):
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
		else:
			print "no result found"
	
	def fetchall(self, query):
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
