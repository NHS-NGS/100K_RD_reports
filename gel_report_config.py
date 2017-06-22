
####################### Authentication ##################
# path to files containing
username =  "/home/mokaguys/Apps/CIP_API/auth_username.txt"
pw = "/home/mokaguys/Apps/CIP_API/auth_pw.txt"

####################### Requests module ##################
#the proxy settings for requests module
proxy={'http':'proxy:80'} # if proxy is not required remove/comment this line do not leave blank

################# report modifications #####################
# Where the patient information template can be found
new_patientinfo_table="/home/mokaguys/Apps/CIP_API/patient_info_table_template.html"
new_clinician_table="/home/mokaguys/Apps/CIP_API/referring_clinic_table_template.html"

# what logo do you want to replace the gel logo with?
new_logo="/home/mokaguys/Apps/CIP_API/images/viapathlogo_white.png"

#report title
report_title="100,000 Genomes Project Rare Disease Primary Findings"

########################### pdfkit ##########################
# path to the wkhtmltopdf executable
wkhtmltopdf_path="/home/mokaguys/Apps/wkhtmltox/bin/wkhtmltopdf"

########################### Report location #################
# Where do you want the outputs?
html_reports="/home/mokaguys/Documents/GeL_reports/html/" # intermediate html files
pdf_dir="/home/mokaguys/Documents/GeL_reports/"