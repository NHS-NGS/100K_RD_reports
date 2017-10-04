####################### Where the App lives##############
app_home="/home/mokaguys/Apps/CIP_API/" # note trailing slash!!

####################### Authentication ##################
# path to files containing
username =  app_home + "auth_username.txt"
pw = app_home + "auth_pw.txt"

####################### Requests module ##################
#the proxy settings for requests module
proxy={'http':'proxy:80'} # if proxy is not required remove/comment this line do not leave blank

################# report modifications #####################
# Where the patient information template can be found
new_patientinfo_table = app_home + "patient_info_table_template.html"
new_clinician_table = app_home + "referring_clinic_table_template.html"

# what logo do you want to replace the gel logo with?
new_logo = app_home + "images/viapathlogo_white.png"

#report title
report_title = "100,000 Genomes Project Rare Disease Primary Findings"

# warning message if there is an error reported when generating the report
warning_message = "Warning! Error making the report.\nIf issue continues for this sample contact GEL Helpdesk @ ssd.servicedesk@nhs.net.\nError message = "

########################### pdfkit ##########################
# path to the wkhtmltopdf executable
wkhtmltopdf_path = "/home/mokaguys/Apps/wkhtmltox/bin/wkhtmltopdf"

########################### Report location #################
# Where do you want the outputs?
html_reports = "/home/mokaguys/Documents/GeL_reports/html/" # intermediate html files
pdf_dir = "/home/mokaguys/Documents/GeL_reports/"