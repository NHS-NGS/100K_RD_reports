# 100K_RD_reports Project Requirements 


## Participants
    - Product owner: all GMCs
    - Team: Aled Jones
    - Stakeholders: GMCs, Genomics England

## Current Status
In Progress

## Purpose
Probands are referred to the 100,000 genomes project by a Genomic Medicine Centre (GMC). Samples are sequenced and sent to a CIP (clinical interpretation partner) for analysis.

GMCs are informed when results are ready. If variants have been found the lab can confirm variants before issuing a report from the lab to the referring clinician.

If no variants have been found a report based on the original GEL negative report is issued, as no interpretation has been performed by the laboratory.

This project aims to take the information from the CIP-API, modify the report as required and create a PDF report which can be issued by the GMC.


## Project Goals & Objectives 
Code was designed to be modular with the hope minimal changes would be required by an GMC to implement this code.

The resulting Appshould:
- Read the CIP-API
- Download the clinical report for the desired proband (using the GEL Participant ID)
- Modify the html report
- Produce pdf that can be sent to referring Clinician

        
## Requirements
This must be easily deployable within all GMCs (taking into account common operating systems and staff expertise) 

## Functional
- Take a GEL participant ID
- Able to differentiate between samples that have been interpreted and confirmed by the lab and where no variants have been found and no interpretation has been performed by the laboratory.

# Technical
- Able to run cross platform
- Use widely supported tools/software where possible
- Uses Python to enable easy adoption and development by any GMC

## Usability
- Modular so can be called by/integrated into other automated systems/user interfaces.
