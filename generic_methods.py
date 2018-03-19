import requests
import yaml
import os


"""
This file will contain methods and variables common to the use of the GEL CIPAPI interface, as well as other resources
This file can be kept in any project where it may be useful, and encourages DRY practices

Alternatively, add this file as an addtional environment variable/PYTHON_PATH variable to use the methods from anywhere

This script assumes that the environment variable file has been created (based on the example credentials in this folder)
and that the populated file is added as an environment variable 'ENV_CREDENTIALS'
"""


def blind_recent_ir_and_version_from_member(member):
    """
    a method which takes a member ID, and returns the most recent interp request and version number

    :param member: 
    :return: 
    """

    cipapi_details = blind_get_gel_credentials_by_app('cip_api')
    member_check_url = get_generic_members_url().format(cipapi=cipapi_details['host'], member=member)

    member_json = get_url_json_response_with_header(member_check_url,
                                                    get_cipapi_header_from_credentials(cipapi_details))

    feedback = {}
    if member_json:
        for result in member_json['results']:
            ir_and_version = result['interpretation_request_id']

            ir, version = ir_and_version.split('-')
            if ir not in feedback:
                feedback[ir] = {'versions': [int(version)]}

            else:
                feedback[ir]['versions'].append(int(version))

            feedback[ir].update({'cip': result['cip'],
                                 'sample_type': result['sample_type'],
                                 'assembly': result['assembly']})

    for ir in feedback:
        feedback[ir]['recent'] = max(feedback[ir]['versions'])

    return feedback


def recent_ir_and_version_from_member_with_details(member, details):
    """
    a method which takes a member ID, and returns the most recent interp request and version number
    :param member:
    :return:
    """

    member_check_url = get_generic_members_url().format(cipapi=details['host'], member=member)

    member_json = get_url_json_response_with_header(member_check_url, get_cipapi_header_from_credentials(details))

    feedback = {}
    if member_json:
        for result in member_json['results']:
            ir_and_version = result['interpretation_request_id']

            ir, version = ir_and_version.split('-')
            if ir not in feedback:
                feedback[ir] = {'versions': [int(version)]}

            else:
                feedback[ir]['versions'].append(int(version))

            feedback[ir].update({'cip': result['cip'],
                                 'sample_type': result['sample_type'],
                                 'assembly': result['assembly']})

    for ir in feedback:
        feedback[ir]['recent'] = max(feedback[ir]['versions'])

    return feedback


def recent_ir_and_version_from_member_with_details_and_header(member, details, header):
    """
    a method which takes a member ID, and returns the most recent interp request and version number
    :param member:
    :return:
    """

    member_check_url = get_generic_members_url().format(cipapi=details['host'], member=member)

    member_json = get_url_json_response_with_header(member_check_url, header)

    feedback = {}
    if member_json:
        for result in member_json['results']:
            ir_and_version = result['interpretation_request_id']

            ir, version = ir_and_version.split('-')
            if ir not in feedback:
                feedback[ir] = {'versions': [int(version)]}

            else:
                feedback[ir]['versions'].append(int(version))

            feedback[ir].update({'cip': result['cip'],
                                 'sample_type': result['sample_type'],
                                 'assembly': result['assembly']})

    for ir in feedback:
        feedback[ir]['recent'] = max(feedback[ir]['versions'])

    return feedback


def get_assumed_env_file():
    """
    checks if the standard env file for credentials exists, returns if true
    :return:
    """

    try:
        if os.path.exists(os.getenv('ENV_CREDENTIALS')):
            return os.getenv('ENV_CREDENTIALS')

        else:
            print 'the standard credentials file cannot be located'
            print 'the environment variable tried was "ENV_CREDENTIALS"'
            raise KeyError('Standard Env file not seen')

    except:
        print('error encountered when trying to find/read the ENV_CREDENTIALS env file')
        return False


def get_url_json_response(url):
    """
    take a URL; return the result as JSON

    :param url:
    :param header:
    :return:
    """

    response = requests.get(url=url)

    if response.status_code != 200:
        raise ValueError(
            "Received status: {status} for url: {url} with response: {response}".format(
                status=response.status_code, url=url, response=response.content)
        )
    return response.json()


def get_url_json_response_with_header(url, header):
    """
    take a URL and an authenticated header; return the result as JSON

    :param url:
    :param header:
    :return:
    """

    response = requests.get(url=url, headers=header)

    if response.status_code != 200:
        raise ValueError(
            "Received status: {status} for url: {url} with response: {response}".format(
                status=response.status_code, url=url, response=response.content)
        )
    return response.json()


def get_panel_list_from_single_ir_json(json):
    """
    for the results of an interpretation-request/ir/version query, get the panels
    example of an in-built highly specific query to prevent re-writing in future
    :param json:
    :return:
    """

    return json['interpretation_request_data']['json_request']['pedigree']['analysisPanels']


def get_pedigree_from_single_ir_json(json):
    """
    retrieve only the pedigree section from an IR JSON

    :param json:
    :return:
    """

    return json['interpretation_request_data']['json_request']['pedigree']


def get_gel_credentials(env_path):
    """
    takes the path to the YAML environment file, and reads out all credential sets it contains
    return in dictionary form

    :param env_path:
    :return:
    """

    # check the file exists
    if not os.path.exists(env_path):
        raise ValueError('The stated file for environment login credentials doesn\'t exist: {}'.format(env_path))

    # open the file and read into python variables
    cred_dict = yaml.load(open(env_path))

    # repackage the list of dictinoaries as a dictionary of dictionaries - reference credentials by name
    credentials = {entry['name']: entry for entry in cred_dict}

    # return the contents in dictionary form
    return credentials


def get_gel_credentials_by_app(env_path, app):
    """
    takes the path to the YAML environment file, and reads out all credentials for <app>
    return in dictionary form

    :param env_path:
    :param app: name of an app with credentials in this file; return only those
    :return:
    """

    # check the file exists
    if not os.path.exists(env_path):
        raise ValueError('The stated file for environment login credentials doesn\'t exist: {}'.format(env_path))

    # open the file and read into python variables
    cred_dict = yaml.load(open(env_path))

    # identify the credential sets which were found, list under the resource name
    credentials = {entry['name']: entry for entry in cred_dict}

    # return the contents in dictionary form
    return credentials[app]


def blind_get_gel_credentials():
    """
    takes the path to the environment file, in YAML format, and reads out all credential sets it contains
    return in dictinoary form
    :param env_path:
    :return:
    """

    # open the file and read into python variables
    cred_dict = yaml.load(open(get_assumed_env_file()))

    # identify the credential sets which were found, list under the resource name
    credentials = {entry['name']: entry for entry in cred_dict}

    # return the contents in dictionary form
    return credentials


def blind_get_gel_credentials_by_app(app):
    """
    takes the path to the environment file, in YAML format, and reads out all credentials for <app>
    return in dictionary form

    'blind' as this works on assumptions about where the environment variable lives and how it is referenced

    :param app: name of an app with credentials in this file; return only those
    :return:
    """

    # open the file and read into python variables
    cred_dict = yaml.load(open(get_assumed_env_file()))

    # identify the credential sets which were found, list under the resource name
    credentials = {entry['name']: entry for entry in cred_dict}

    # return the contents in dictionary form
    return credentials[app]


def get_cipapi_header(url, username, password):
    """
    manually send login details to get a header for the cipapi
    could feasibly provide tokens for any other JWT service using get-token interface

    :param url:
    :param username:
    :param password:
    :return:
    """

    auth_endpoint = "/get-token/"

    irl_response = requests.post(
        url=url + auth_endpoint,
        json=dict(
            username=username,
            password=password,
        ),
    )
    irl_response_json = irl_response.json()
    token = irl_response_json.get('token')

    auth_header = {
        'Accept': 'application/json',
        "Authorization": "JWT {token}".format(token=token),
    }
    return auth_header


def get_cipapi_header_from_credentials(credentials):
    """
    takes the environment variables for the cip api in dictionary form and goes to get the authenticated header

    :param credentials: the env variables dict
    :return:
    """

    url = credentials['host']
    username = credentials['username']
    password = credentials['password']
    auth_endpoint = "/get-token/"

    irl_response = requests.post(
        url=url + auth_endpoint,
        json=dict(
            username=username,
            password=password,
        ),
    )
    irl_response_json = irl_response.json()
    token = irl_response_json.get('token')

    auth_header = {
        'Accept': 'application/json',
        "Authorization": "JWT {token}".format(token=token),
    }
    return auth_header


def get_opencga_sid(credentials):
    """
    a generic method for getting a valid session ID in opencga using the REST API

    :param credentials:
    :return:
    """

    endpoint_ext = '/users/{username}/login/'.format(
        username=credentials['username']
    )
    full_url = credentials['host'] + endpoint_ext

    sid_response = requests.post(
        url=full_url,
        json=dict(
            password=credentials['password']
        )
    )

    if sid_response.status_code != 200:
        raise ValueError(
            "Received status: {status} for url: {url} with response: {response}".format(
                status=sid_response.status_code, url=full_url, response=sid_response.content)
        )

    json_response = sid_response.json()
    for response in json_response['response']:
        if response['numResults'] == 1:
            for result in response['result']:
                return result['sessionId']


def complete_sid_process():
    """
    everything required to generate a SID for OpenCGA, chained together for simplicity
    :return:
    """

    return get_opencga_sid(blind_get_gel_credentials_by_app('opencga_rest'))



def return_study_from_assembly_and_type(assembly, disease, somatic=False):
    """
    returns a study ID, or returns False

    :param assembly:
    :param disease:
    :return:
    """

    if assembly == 'GRCh37':

        if disease == 'raredisease':
            return '1000000024'

        elif disease == 'cancer':
            if somatic:
                return '1000000030'
            else:
                return '1000000026'

        else:
            return False

    elif assembly == 'GRCh38':

        if disease == 'raredisease':
            return '1000000032'

        elif disease == 'cancer':
            if somatic:
                return '1000000038'
            else:
                return '1000000034'

        else:
            return False

    else:
        return False


def get_generic_single_ir_url():
    """
    commonly used URL

    :return: a URL template for getting the JSON results for a single IR and Version
    """

    return '{cipapi}/interpretation-request/{ir}/{ver}/'


def get_generic_single_file_url():
    """

    :return: a URL template for getting a single file for this sample and study
    """
    return '{opencga}/files/{file}/info?sid={sid}&study={study}&lazy=true'


def get_generic_sample_study_url():
    """

    :return: a URL template for getting the study this sample is in
    """
    return '{opencga}/studies/{study}/samples?sid={sid}&name={name}'


def get_generic_members_url():
    """

    :return: a URL template for getting the details of an individual based on their member/Proband ID
    """
    return '{cipapi}/interpretation-request?format=json&members={member}'
