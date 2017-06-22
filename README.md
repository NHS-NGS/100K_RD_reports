# Generating patient reports using the GEL CIP API
This is a Python script which takes a GEL participantID and queries the GEL CIP-API to return a clinical report which is then modified and converted into a PDF.
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
Using the Python requests module and the access token generated above the CIP-API is read, returning all patients that your token allows you to access.
#### Selecting which report to return
Once the Participant ID is found a few checks are performed to ensure the correct report is found.
1. **If the patient status is blocked no report will be returned**
2. Reports can be generated from multiple versions of the CIP version. **The report from the most recent version CIP version is taken**
3. There can also be multiple reports generated for each version of the CIP. **The most recent report is taken.**
#### Modification of the report
Where possible the Python module Beautiful soup is used to modify the html as an python object. The CSS cannot be modified in this way so is modified a bit more crudely, by parsing the html file, identifying the required section of the report and replacing the text.

The report is edited to remove the small grey banner containing the date report generated and the GEL participant ID.

The large green banner from the top of the report (containing the GEL logo and banner) is also removed, replaced with a space for the referring clinician information (using the referring_clinic_table_template), a new report title and the labs logo (both defined in the config file).
The GeL address and is also removed top of the report.

The coverage section is then modified so it is always expanded (removing the click to expand option)

A new table is also inserted above the participant information table to be populated with additional patient information. This uses the template found in the patient_info_table_template.html.

A page break is also added before the reference databases and software versions to prevent page breaks mid table.


#### Adding patient information from local LIMS system
This table is then populated by a function which queries the LIMS system. This will need to be adapted by each lab locally.

pyODBC can be used to connect and query SQL databases. functions which query the database and returns the result have been included in the script (with usage instrutions).

The database connection details are stored separately and imported to the script to enable the script to be stored openly in github. 

An example database connection string (that works with pyODBC) can be found in the file database_connection_config.py. 

This function must essentially populate a dictionary containing one entry for each item in the patient_info_table_template.html eg patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender,"clinician":clinician,"clinician_add":clinic_address,"report_title":report_title}

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

It can be installed via apt-get **HOWEVER THIS VERSION CANNOT RUN IN HEADLESS MODE**  - This may however be a useful exercise to install dependancies!

	sudo apt-get install wkhtmltopdf
	
	sudo apt-get remove wkhtmltopdf

A version that can be run headless was downloaded using wget

	wget https://downloads.wkhtmltopdf.org/0.12/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

	tar xpvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

Further dependancies were required:

	sudo apt-get install libxrender1 libfontconfig

## Usage
python get_report.py -g 12345678
