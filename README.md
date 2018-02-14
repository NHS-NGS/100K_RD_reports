# Generating patient reports using the GEL CIP API
This is a Python script which takes a GEL participantID and queries the GEL CIP-API to return a clinical report which is then modified and converted into a PDF.

The GEL html report is used, but modified depending on the result of the test. 
- If variants were found which were investigated by the lab the report is modified to look like the lab is issuing this report.
- If the lab has not investigated any variants the original GEL headers are left on the report, with the only addition being a table with extra patient information included.

## How it works
As described below the following files and settings are required:
- Files containing a username and password to authenticate with the CIP API
- Settings in the config file changed as required 
- A file containing the database connection credentials to be used by pyODBC
- The desired patient demographics extracted from local LIMS system

#### Authentication
The script authentication.py creates an JSON web token (JWT) using the username and passwords provided in the files auth_pw.txt and auth_username.txt.

Each file should just contain a single line containing only the username or password.

#### Reading the API
Using the Python requests module and the access token generated above the CIP-API interpretationrequestlist endpoint is read, returning all records which have:
* a status of sent_to_gmcs,report_generated or report_sent
* proband ID = the proband ID specified (see usage)
* CIP = the CIP specified in the config file

#### Selecting which report to return
There may be multiple interpretation requests per proband, however there should only be one interpretation request for the given CIP and status described above (an error is raised if this is False).
There can be multiple versions of the report. **The most recent report is taken.**

#### Checks and warnings
In some cases the report contains an error warning that it cannot find coverage data, or annotation data. These issues are usually fleeting and may resolve themselves after a short time, however if this is not the case the GEL helpdesk should be contacted. The script can be stopped at this point if required.

#### Modification of the report
Where possible the Python module Beautiful soup is used to modify the html as an python object. However, the CSS cannot be modified in this way so this is altered a bit more crudely, by parsing the html file, identifying the required section of the report and replacing the text.

A new table is also inserted above the participant information table to be populated with additional patient information. This uses the template found in the patient_info_table_template.html.

For reports that are issued by the lab:
- The report is edited to remove the small grey banner containing the date report generated and the GEL participant ID.
- The large green banner from the top of the report (containing the GEL logo and banner) is also removed, replaced with a space for the referring clinician information (using the referring_clinic_table_template), a new report title and the labs logo (both defined in the config file).
- The GeL address and is also removed top of the report.
- The coverage section is then modified so it is always expanded (removing the click to expand option)
- A page break is also added before the reference databases and software versions to prevent page breaks mid table.


#### Adding patient information from local LIMS system
This table is then populated by a function which queries the LIMS system. This will need to be created locally by each lab.

pyODBC can be used to connect and query SQL databases. Functions which query the database and returns the result have been included in the script (with usage instructions).

The database connection details are stored separately and imported to the script to enable the script to be stored openly in github. 

An example database connection string (that works with pyODBC) can be found in the file database_connection_config.py. 

This function must essentially populate a dictionary containing one entry for each item in the patient_info_table_template.html eg patient_info_dict={"NHS":NHS,"InternalPatientID":InternalPatientID,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender,"clinician":clinician,"clinician_add":clinic_address,"report_title":report_title}

These templates (and dictionary) can be modified as required.
#### Output
A pdf and the intermediary html files are produced in the locations specified in the config file.

These files are named GelParticipantID.pdf (eg 12345678.pdf).
## Requirements
This has been developed and tested on a Linux server(Ubuntu 16.04) connected to an N3 network.

#### Python
The following Python packages are required:

- beautifulsoup4 
- jinja2 
- pyODBC 
- requests
- pdfkit ^ 

^ This must be installed via pip
 
	pip install pdfkit

#### wkhtmltopdf
This is the software used by pdfkit to convert html to pdf.

It can be installed via apt-get **HOWEVER THIS VERSION (v9.9) CANNOT RUN IN HEADLESS MODE**  - This may be a useful exercise to install dependancies, however as described below I still had to download some dependancies!

	sudo apt-get install wkhtmltopdf
	
	sudo apt-get remove wkhtmltopdf

A version that can be run headless was downloaded using wget

	wget https://downloads.wkhtmltopdf.org/0.12/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

	tar xpvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

Further dependancies were required:

	sudo apt-get install libxrender1 libfontconfig

## Usage
-g, --gelid: 	GEL participantID eg 12345678

-h, --removeheader: 	If the report headers should be removed to look like the lab is issuing the report (True). False does not alter the header, but does include the patient information table.

	python get_report.py -g 12345678 -h True
	python get_report.py -g 12345678 -h False
