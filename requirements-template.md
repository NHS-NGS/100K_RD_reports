# GEL_reports Project Requirements 


## Participants

    - Product owner: GMCs
    - Team: Aled Jones
    - Stakeholders: GMCs, Genomics England

## Current Status
Approved

## Purpose
Probands are referred to the 100,000 genomes project by a Genomic Medicine Centre (GMC). Samples are sequenced and sent to a CIP (clinical interpretation partner) for analysis.

Using the CIP portal Clinical Scientists within the GMC must decide which (if any) variants to confirm and create a clinical report.

The GMC would then issue a report to the referring clinician.


This project aims to take the information from the clinical report, modify the report so it is clear the report is not being issued by GEL and create a PDF report which can be issued by the GMC.


## Project Goals & Objectives 
Code was designed to be modular with the hope minimal changes would be required by an GMC to implement this code

    Goals
        - Read the CIP-API
        - Download the clinical report for the desired proband (using the GEL Participant ID)
        - Modify the html report to 
            - Replace GEL Logo with laboratory Logo (and UKAS accreditation logo?)
            - Remove GEL address
            - Add in patient demographics
            - Ensure the coverage statistics are visible

    Out of scope / non goals
        - Each GMC will require some modification to the code to fit in with local requirements eg:
            - Connect to local LIMS
            - Add in Logo
        
## Requirements
This has been developed and tested on a Linux server (Ubuntu 16.04) connected to an N3 network.

#### Python
Python (v2.7) with the following packages is required:

    beautifulsoup4 (4.5.3)
    jinja2 (2.9.6)
    pyODBC (3.0.10)
    requests (2.13.0)
    pdfkit (0.6.1)

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


| Requirement | Description | Acceptance Criteria | Priority | GitHub Issue(s) |
|-------------|-------------|---------------------|----------|-----------------|
|             |             |                     |          |                 |
|             |             |                     |          |                 |
|             |             |                     |          |                 |

### Functional
The following files and settings are required:

- Files containing a username and password to authenticate with the CIP API
- Config file changed as required 
- A file containing the database connection credentials to be used by pyODBC
- The desired patient demographics extracted from local LIMS system
##### Authentication
The script authentication.py creates an JSON web token (JWT) using the username and passwords provided in the files auth_pw.txt and auth_username.txt.

Each file should just contain a single line containing only the username or password. Example files are provided (dummy_auth_pw.txt and dummy_auth_username.txt).
##### Reading the API
Using the Python requests module and the access token generated above the interpretationRequestList endpoint is read, returning all patients that your token allows you to access.
##### Selecting which report to return
Once the Participant ID is found a few checks are performed to ensure the correct report is found.
1. **If the patient status is blocked no report will be returned**
2. Reports can be generated from multiple versions of the CIP version. **The report from the most recent version CIP version is taken**
3. There can also be multiple reports generated for each verison of the CIP. **The most recent report is taken.**
##### Modification of the report
Where possible the Python module Beautiful soup is used to modify the html. The CSS is modified a bit more crudely, by reading the file, identifying the required section of the report and replacing the text.

The report is edited to remove the GEL logo and the GEL Address from near the top of the report. This is replaced by a logo of your chosing (stated in the config file)

The coverage section is then modified so it is always expanded (removing the click to expand option)

The colour of the report header is modified by altering the CSS (the new colour can be specified in the config file)

A new table is also inserted above the participant information table to be populated with additional patient information. This uses the template found in the patient_info_table_template.html.
##### Adding patient information from local LIMS system
This table is then populated by a function which queries the LIMS system. This will need to be adapted by each lab locally.

pyODBC can be used to connect and query SQL databases.

The database connection details are stored seperately and imported to the script to enable the script to be stored publically in github. 

An example database connection string (that works with pyODBC) can be found in the file dummy_database_connection_config.py. 

This function must essentially populate a dictionary containing one entry for each item in the patient_info_table_template.html eg patient_info_dict={"NHS":NHS,"PRU":PRU,"dob":DOB,"firstname":FName,"lastname":LName,"gender":Gender}

This template (and dictionary) can be modified as required.
##### Output
A pdf and the intermediary html files are produced in the locations specified in the config file.

These files are named GelParticipantID.pdf (eg 12345678.pdf).

### Usability 
python get_report.py -g 12345678
