"""
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Copyright © `2023` `Microsoft Corporation`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

This server is a Flask http web server that hosts the http rest endpoints that are the client API for the DIFI checker/decoder (drx.py)

This Flask http server is meant to run alongside the drx.py, which is a socket server that receives and processes the packets

You don't need to run the webgui to use the DIFI validator functionality, it simply adds a convenient web GUI interface for it

API Examples:
curl -k http://<machine>:5000/api/v1/difi/compliant/standardcontext/00000001
curl -k http://<machine>:5000/api/v1/difi/compliant/versioncontext/00000001
curl -k http://<machine>:5000/api/v1/difi/compliant/data/00000001
curl -k http://<machine>:5000/api/v1/difi/compliant/count/00000001
curl -k http://<machine>:5000/api/v1/difi/noncompliant/00000001
curl -k http://<machine>:5000/api/v1/difi/noncompliant/count/00000001
curl -k http://<machine>:5000/api/v1/difi/help/api
curl -k http://<machine>:5000/api/v1/difi/version
"""

from __future__ import annotations #takes care of forward declaration problem for type hints/annotations (so don't have to put quotes around types)

import subprocess
from subprocess import CalledProcessError
import sys
import json
import os
import pprint
import psutil
import re
from flask import Flask, jsonify, request, redirect, render_template, Response, session, url_for
from markupsafe import Markup
from urllib.parse import urlparse
from datetime import timezone, datetime

from difi_utils.difi_constants import *

app = Flask(__name__)

###########
#config
###########
DIFI_VERSION_SUPPORTED = "v1"
DIFI_CACHE_HOME = "./"
if os.getenv("DIFI_CACHE_HOME") != "":
    DIFI_CACHE_HOME = os.getenv("DIFI_CACHE_HOME") + "/"
CONFIG_SETTINGS = "config.json"
VERSION_INFO = "version-info.json"

#openapi
DIFI_NAME = "DIFI Validator"
DIFI_DESCRIPTION = "DIFI packet decoder and sender"
DIFI_VERSION_MAJOR = 1
DIFI_VERSION_MINOR = 1
DIFI_VERSION_PATCH = 0
DIFI_VERSION_BUILD = "0"
DIFI_START_TIME = datetime.now(timezone.utc).isoformat()

#makes json returned in responses pretty print with nice indenting, etc.
#TODO: comment out in production
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

#if redirect back to form, then store previous form in session
#app.secret_key = "our_secret_key"

###########
#error types
###########
class InvalidStreamId(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)

class StreamIdListFailure(Exception):
    pass


##################
#helper functions
##################
def get_packet_hex(output):
    res=""
    output_line = output.find("Packet output: ")

    if output_line != -1:
        end_of_output = output.find("\n", output_line+1)
        if end_of_output != -1:
          res = output[output_line+15:end_of_output]

    return res

def shorten_packet_field(field_name):
    if field_name == 'packet-type':
        field_name = 'pkt-type'
    elif field_name == 'sequence-number':
        field_name = 'seqnum'
    elif field_name == 'reserved':
        field_name = 'rsvd'
    elif field_name == 'packet-size':
        field_name = 'pkt-size'
    elif field_name == 'dpf-report-index':
        field_name = 'dpf-rpt-ind'
    elif field_name == 'reference-level':
        field_name = 'ref-level'
    elif field_name == 'rf-reference-frequency':
        field_name = 'rf-ref-freq'
    elif field_name == 'if-reference-frequency':
        field_name = 'if-ref-freq'

    return field_name

def read_noncompliant_from_file(stream_id):
    
    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-noncompliant-00000001.dat"
    fname = "%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_NONCOMPLIANT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        buf = f.read()
        return buf

def read_noncompliant_count_from_file(stream_id):
    
    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-noncompliant-count-00000001.dat"
    fname = "%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        d = {}
        d["count"] = 0
        d["updated"] = ""
        buf = f.read()
        if len(buf) > 0:
            entry = buf.split("#", 1)
            d["count"] = int(entry[0])
            if len(entry) > 1:
                d["updated"] = entry[1]
        return d

def read_compliant_standard_context_from_file(stream_id):

    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-compliant-standard-context-00000001.dat"
    fname = "%s%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_COMPLIANT_FILE_PREFIX, DIFI_STANDARD_CONTEXT, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        buf = f.read()
        return buf

def read_compliant_version_context_from_file(stream_id):

    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-compliant-version-context-00000001.dat"
    fname = "%s%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_COMPLIANT_FILE_PREFIX, DIFI_VERSION_CONTEXT, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        buf = f.read()
        return buf

def read_compliant_data_from_file(stream_id):

    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-compliant-data-00000001.dat"
    fname = "%s%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_COMPLIANT_FILE_PREFIX, DIFI_DATA, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        buf = f.read()
        return buf

def read_compliant_count_from_file(stream_id):
    
    #TODO: in the future switch to read from kafka or database here instead...

    #fname = "difi-compliant-count-00000001.dat"
    fname = "%s%s%s%s" % (DIFI_CACHE_HOME, DIFI_COMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
    with open(fname, 'r', encoding="utf-8") as f:
        d = {}
        d["count"] = 0
        d["updated"] = ""
        buf = f.read()
        if len(buf) > 0:
            entry = buf.split("#", 1)
            d["count"] = int(entry[0])
            if len(entry) > 1:
                d["updated"] = entry[1]
        return d

def put_settings(data):
    fname = "%s%s" % (DIFI_CACHE_HOME, CONFIG_SETTINGS)
    with open(fname, 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_settings():
    fname = "%s%s" % (DIFI_CACHE_HOME, CONFIG_SETTINGS)
    with open(fname, 'r', encoding="utf-8") as f:
        return json.load(f)

def get_version_info():
    fname =VERSION_INFO
    if os.path.isfile(fname):
        with open(fname, 'r', encoding="utf-8") as f:
            return json.load(f)

    default_version = {
        "major": DIFI_VERSION_MAJOR,
        "minor": DIFI_VERSION_MINOR,
        "patch": DIFI_VERSION_PATCH,
        "build": DIFI_VERSION_BUILD
    }
    return default_version

def get_difi_noncompliant_file_stream_ids() -> dict:

    #TODO: in the future switch to read from kafka or database here instead...

    d = {}
    try:
        l = []
        with os.scandir(path=DIFI_CACHE_HOME) as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        stream_id = entry.name.replace(DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, "", 1)
                        stream_id = stream_id.replace(DIFI_FILE_EXTENSION, "", 1)
                        l.append(stream_id)

        d["stream_id_list"] = l

    except Exception as e:
        print("error getting non-compliant file stream ids -->")
        pprint.pprint(e)
        raise StreamIdListFailure()
    return d

def get_difi_compliant_file_stream_ids() -> dict:

    #TODO: in the future switch to read from kafka or database here instead...

    d = {}
    try:
        l = []
        with os.scandir(path=DIFI_CACHE_HOME) as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        stream_id = entry.name.replace(DIFI_COMPLIANT_COUNT_FILE_PREFIX, "", 1)
                        stream_id = stream_id.replace(DIFI_FILE_EXTENSION, "", 1)
                        l.append(stream_id)

        d["stream_id_list"] = l

    except Exception as e:
        print("error getting compliant file stream ids -->")
        pprint.pprint(e)
        raise StreamIdListFailure()
    return d

def validate_stream_id(stream_id: str):
    if len(stream_id) != 8 and len(stream_id) != 12:
        raise InvalidStreamId("stream id [%s] not valid, must be an 8 digit hex string (example: 00000001) or 'no-stream-id'" % stream_id)

def validate_jsonify_response(jsonify_response: tuple):
    if type(jsonify_response) is not tuple:
        raise Exception(message="Internal source function must return type 'tuple'.")
    elif type(jsonify_response[0]) is not Response:
        raise Exception(message="Internal source function must return response object type 'Response' for first element in 'tuple'.")
    elif type(jsonify_response[1]) is not int:
        raise Exception(message="Internal source function must return 'status code' type 'int' for second element in 'tuple'.")

    #status code 200 OK is valid, all other status codes raise error (i.e. 500, 503, etc.)
    if jsonify_response[1] != 200:
        raise Exception(message="Unable to render HTML template page. The server return Status Code = [%d]" % (jsonify_response[1]))

def is_template_route(url_rule):
    return getattr(url_rule, 'is_template_route', False)

def highlight_bad_field_in_exception(stderr: str, e: Exception) -> str:

    s = str(e)
    try:
        result = re.search(r"\bFIELDS\[\"--.*?\"\]", stderr)
        if result is not None:
            found = result.group(0)
            found = found.replace("FIELDS[\"", "")
            found = found.replace("\"]", "")
            s = s.replace(found, '<span style="color:red; font-style: italic;">' + found + '</span>')
    except Exception:
        pass
    return s

####################
#html template helper functions
####################
@app.template_filter('difi_check')
def difi_check(l: list, default_class="d"):
    if l is not None and type(l) is list and type(l[0]) is str and type(l[1]) is bool:
        if default_class == "d":
            if l[1] == False:
                return 'dred'
            else:
                return 'dblue'
        elif default_class == "dsf":
            if l[1] == False:
                return 'dsfred'
            else:
                return 'dsfblue'
        elif default_class == "dsf2":
            if l[1] == False:
                return 'dsf2red'
            else:
                return 'dsf2blue'
        else:
            return default_class
    else:
        return default_class

@app.template_filter('title_check')
def title_check(l: list):
    if l is not None and type(l) is list and type(l[0]) is str:
        return l[0]
    else:
        return ''

####################
#html template formatters
####################
def is_hex(value: str) -> bool:
    """Returns whether the specified string value is valid hex. (i.e. '0x7BB98000','0x4','8000000c',etc)"""
    try:
        int(value,16)
        return True
    except ValueError:
        return False

def check_hex(value: str) -> str:
    """Validates whether the specified string value is valid hex (i.e. '0x7BB98000','0x4','8000000c',etc) and if valid returns that specified string, if not valid returns error string."""
    try:
        int(value,16)
        return value
    except ValueError:
        return "##err"

@app.template_filter()
def hex1(value, validate=True):
    return "0x%1x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex2(value, validate=True):
    return "0x%02x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex4(value, validate=True):
    return "0x%04x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex6(value, validate=True):
    return "0x%06x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex7(value, validate=True):
    return "0x%07x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex8(value, validate=True):
    return "0x%08x" % value if type(value) is int else check_hex(value) if validate==True else value
@app.template_filter()
def hex(value, digits: str, validate=True):
    #remember digits needs to include 2 more in count for prefix '0x'
    if type(value) is int:
        s = "{:#" + str(digits) + "x}"
        return s.format(value)
    else:
        if validate==True:
            return check_hex(value)
        else:
            return value

####################
#custom decorators
####################
#custom decorator for html template route
def template_route(route, **options):
    def decorator(f):
        if os.getenv("DIFI_UI") != "disable":
            app.add_url_rule(route, view_func=f, **options)

            #adds item to rule object indicating this rule is an html template route
            for rule in app.url_map.iter_rules():
                if rule.rule == route:
                    setattr(rule, "is_template_route", True)
                    break

        return f
    return decorator



####################
#api route handlers - (REST json / HTML GUI's)
####################
@app.route('/api/v1/difi/noncompliant/<string:stream_id>', methods=['GET'])
@template_route('/web/v1/difi/noncompliant/<string:stream_id>', methods=['GET'])
def get_difi_noncompliant(stream_id):

    """Gets field comparison matrix of DIFI related packet field values for the specified stream id with their associated 'required value/current value' pairs which caused the packet to be considered 'non-compliant' with the DIFI standard.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        validate_stream_id(stream_id)

        data = read_noncompliant_from_file(stream_id)
        data_dict = json.loads(data)
        data_most_recent = data_dict[-1] # pull out most recent packet
        if is_template_route(request.url_rule):
            return render_template('noncompliant.html', **data_most_recent)
        else:
            return jsonify(json.loads(data)), 200

    except InvalidStreamId as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % e.message))
        else:
            return jsonify(error_code=500, message=e.message), 500
    except FileNotFoundError as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message="No data found for stream id [%s]." % (stream_id))
        else:
            return jsonify(message="No data found for stream id [%s]." % (stream_id)), 200
    #except TemplateNotFound as e:
    #    return render_template('msg.html', message="No html template page found on server. [%s]" % (str(e)))
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/noncompliant/count/<string:stream_id>', methods=['GET'])
@template_route('/web/v1/difi/noncompliant/count/<string:stream_id>', methods=['GET'])
def get_difi_noncompliant_count(stream_id):

    """Gets the total count of 'non-compliant' packets archived for the specified stream id.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        validate_stream_id(stream_id)

        data = read_noncompliant_count_from_file(stream_id)

        if is_template_route(request.url_rule):
            data["stream_id"] = stream_id
            data["caption"] = "Non-Compliant"
            return render_template('count.html', **data)
        else:
            return jsonify(data), 200

    except InvalidStreamId as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % e.message))
        else:
            return jsonify(error_code=500, message=e.message), 500
    except FileNotFoundError as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message="No data found for stream id [%s]." % (stream_id))
        else:
            return jsonify(message="No data found for stream id [%s]." % (stream_id)), 200
    #except TemplateNotFound as e:
    #    return render_template('msg.html', message="No html template page found on server. [%s]" % (str(e)))
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/compliant/<string:packet_type>/<string:stream_id>', methods=['GET'])
@template_route('/web/v1/difi/compliant/<string:packet_type>/<string:stream_id>', methods=['GET'])
def get_difi_compliant_packet(stream_id, packet_type):

    """Gets the most recent compliant packet_type archived for the specified stream id
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        validate_stream_id(stream_id)
        if packet_type == 'standardcontext':
            data = read_compliant_standard_context_from_file(stream_id)
        elif packet_type == 'versioncontext':
            data = read_compliant_version_context_from_file(stream_id)
        elif packet_type == 'data':
            data = read_compliant_data_from_file(stream_id)
        else:
            e = 'bad URL'
            if is_template_route(request.url_rule):
                return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
            else:
                return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500
            
        data_dict = json.loads(data)
        data_most_recent = data_dict[-1] # pull out most recent packet
        if is_template_route(request.url_rule):
            return render_template('compliant.html', **data_most_recent)
        else:
            return jsonify(json.loads(data)[-1]), 200

    except InvalidStreamId as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % e.message))
        else:
            return jsonify(error_code=500, message=e.message), 500
    except FileNotFoundError as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message="No data found for stream id [%s]." % (stream_id))
        else:
            return jsonify(message="No data found for stream id [%s]." % (stream_id)), 200
    #except TemplateNotFound as e:
    #    return render_template('msg.html', message="No html template page found on server. [%s]" % (str(e)))
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/compliant/count/<string:stream_id>', methods=['GET'])
@template_route('/web/v1/difi/compliant/count/<string:stream_id>', methods=['GET'])
def get_difi_compliant_count(stream_id):

    """Gets the total count of 'compliant' packets archived for the specified stream id.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        validate_stream_id(stream_id)

        data = read_compliant_count_from_file(stream_id)

        if is_template_route(request.url_rule):
            data["stream_id"] = stream_id
            data["caption"] = "Compliant"
            return render_template('count.html', **data)
        else:
            return jsonify(data), 200

    except InvalidStreamId as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % e.message))
        else:
            return jsonify(error_code=500, message=e.message), 500
    except FileNotFoundError as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message="No data found for stream id [%s]." % (stream_id))
        else:
            return jsonify(message="No data found for stream id [%s]." % (stream_id)), 200
    #except TemplateNotFound as e:
    #    return render_template('msg.html', message="No html template page found on server. [%s]" % (str(e)))
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/noncompliant', methods=['GET'])
@template_route('/web/v1/difi/noncompliant', methods=['GET'])
def get_difi_noncompliant_streamids():

    """Gets the list of stream id's available to choose from for the 'non-compliant' packet archive.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        if is_template_route(request.url_rule):
            data = get_difi_noncompliant_file_stream_ids()
            data["caption"] = "Non-Compliant"
            data["stream_id_list"] = sorted(data["stream_id_list"])
            return render_template('ids.html', ids=data)
        else:
            return jsonify(get_difi_noncompliant_file_stream_ids()), 200

    except StreamIdListFailure as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % "failed to get stream id list for non-compliant packets."))
        else:
            return jsonify(error_code=500, message="failed to get stream id list for non-compliant packets."), 500
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/compliant', methods=['GET'])
@template_route('/web/v1/difi/compliant', methods=['GET'])
def get_difi_compliant_streamids():

    """Gets the list of stream id's available to choose from for the 'compliant' packet archive.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        if is_template_route(request.url_rule):
            data = get_difi_compliant_file_stream_ids()
            data["caption"] = "Compliant"
            data["stream_id_list"] = sorted(data["stream_id_list"])
            return render_template('ids.html', ids=data)
        else:
            return jsonify(get_difi_compliant_file_stream_ids()), 200
    except StreamIdListFailure as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("%s\r\n" % "failed to get stream id list for compliant packets."))
        else:
            return jsonify(error_code=500, message="failed to get stream id list for compliant packets."), 500
    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/version', methods=['GET'])
def get_difi_version():

    """Gets the DIFI version string that is supported for the URL."""

    try:
        d = {}
        d["version"] = DIFI_VERSION_SUPPORTED
        return jsonify(d), 200
    except Exception as e:
        return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/help/api', methods=['GET'])
@template_route('/web/v1/difi/help/api', methods=['GET'])
def get_difi_api_routes():

    """Gets list of available rest endpoints in API and web interface endpoints.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        routes = {}
        for rule in app.url_map.iter_rules():

            if rule.endpoint != 'static':

                methods = ' '.join(filter(lambda x: x=='GET' or x=='POST' or x=='PUT' or x=='DELETE', rule.methods))

                #build web route description string (prepend html blurb, remove end of docstring that states route return types)
                if getattr(rule, 'is_template_route', False):
                    comment = "" if app.view_functions[rule.endpoint].__doc__ is None else re.sub(":Returns:.*", "", app.view_functions[rule.endpoint].__doc__, flags=re.DOTALL)
                    comment = ''.join(("HTML web page response: ", comment))
                #build api route description string (prepend json blurb, remove end of docstring that states route return types)
                else:
                    comment = "" if app.view_functions[rule.endpoint].__doc__ is None else re.sub(":Returns:.*", "", app.view_functions[rule.endpoint].__doc__, flags=re.DOTALL)
                    #don't prepend json blurb if route is web route or home page
                    if not rule.rule.startswith("/web") and rule.rule != "/":
                        comment = ''.join(("JSON document response: ", comment))

                if methods == "":
                    routes[str(rule)] = "%s" % comment.strip()
                else:
                    routes[str(rule)] = "[%s] %s" % (methods, comment.strip())

        if is_template_route(request.url_rule):
            return render_template('api.html', api={key : routes[key] for key in sorted(routes)})
            #return render_template('api.html', **routes)
        else:
            return jsonify(routes), 200

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


####################
#api route handlers - (HTML GUI's only)
####################
@app.route('/', methods=['GET'])
def get_home_page():

    """Home page - DIFI Validator."""

    try:
        o = urlparse(request.base_url)

        if os.getenv("DIFI_RX_PORT"): 
            porta=os.getenv("DIFI_RX_PORT")
        else:
            porta=4991

        if os.getenv("DIFI_UI") != "disable":
            return render_template('index.html', ip=o.hostname, port=porta)
        else:
            return jsonify(error_code=500, message="User interface not available"), 500
    except Exception as e:
        return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))


@app.route('/web/v1/difi/send/standard-context', methods=['GET', 'POST'])
@app.route('/api/v1/difi/send/standard-context', methods=['POST'])
def send_standard_context_packets():

    """HTML web page used to send 'Standard Context' packets to a target IP address."""

    is_json = request.content_type.find("application/json") if request.content_type else False

    try:
        #if 'POST'
        if request.method == "POST":

            cmd = []
            cmd.append("python3")
            cmd.append("dcs.py")
            if is_json == -1:
                for key,value in request.form.items():

                    if value is not None and value != "" and key.lower().startswith("--"):
                        #key is expected to have '--' on front,
                        #html elements named the same as dcs.py script args
                        #even though is brittle in order to help make it
                        #easier to spot when missing or incorrect
                        cmd.append(key)
                        cmd.append(value)
            else:
                data = request.get_json();

                settings_data = get_settings()
                if settings_data["transmitEnabled"] == False:
                    return jsonify(error_code=400, message="Unable to submit packet while transmit is disabled."), 400
                if not "address" in data:
                    data["address"] = settings_data["transmitHost"];
                if not "port" in data:
                    data["port"] = settings_data["transmitPort"];
                for key, value in data.items():
                    cmd.append("--" + shorten_packet_field(key))
                    cmd.append(str(value))

            # turn on debug
            cmd.append("--debug")
            cmd.append("True")

            #will raise CalledProcessError if sub process has non-zero exit code, instead of success message below
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")

            if is_json != -1:
                packet = get_packet_hex(output)
                if packet != '':
                    data["packet"] = packet

            if is_json == -1:
                return render_template('msg.html', message=Markup("Successfully sent DIFI packet.  <i>(To send more using the same field values, press 'Back' arrow in browser to return to the send page.)</i>"))
            else:
                return jsonify(data), 200

            #if redirect back to form, then store previous form in session
            #session["form_data"] = request.form
            #return redirect(request.url)
            #return redirect(request.referrer)


        #if not 'POST' (i.e. just regular 'GET')
        params = {}

        #if redirect back to form, then store previous form in session
        #form_data = session.get("form_data", None)
        #if form_data:
        #    params = form_data
        #    session.pop("form_data")

        #attempt to pre-fill target host/port in html page with host/port of flask and drx.py servers
        params["send_host"] = None if request.headers.get("Host") is None else request.headers.get("Host").split(':')[0]
        params["send_port"] = 4991
        if os.getenv("DIFI_RX_PORT"):
            params["send_port"] = os.getenv("DIFI_RX_PORT")
        return render_template('send_standard_context.html', **params)

        #if redirect back to form, then store previous form in session
        #return render_template('send_standard_context.html', form=params)
        #
        #in html page:
        #<input value="{{form["--bandwidth"]|default('0.00000095')}}"...

    except CalledProcessError as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))))
        else:
            return  jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))), 500
    except Exception as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure you entered an IP address and port and that all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/web/v1/difi/send/version-context', methods=['GET', 'POST'])
@app.route('/api/v1/difi/send/version-context', methods=['POST'])
def send_version_context_packets():

    """HTML web page used to send 'Version Context' packets to a target IP address."""

    is_json = request.content_type.find("application/json") if request.content_type else False

    try:
        #if 'POST'
        if request.method == "POST":

            cmd = []
            cmd.append("python3")
            cmd.append("dvs.py")
            if is_json == -1:
                for key,value in request.form.items():

                    if value is not None and value != "" and key.lower().startswith("--"):
                        #key is expected to have '--' on front,
                        #html elements named the same as dvs.py script args
                        #even though is brittle in order to help make it
                        #easier to spot when missing or incorrect
                        cmd.append(key)
                        cmd.append(value)
            else:
                data = request.get_json();

                settings_data = get_settings()
                if settings_data["transmitEnabled"] == False:
                    return jsonify(error_code=400, message="Unable to submit packet while transmit is disabled."), 400
                if not "address" in data:
                    data["address"] = settings_data["transmitHost"];
                if not "port" in data:
                    data["port"] = settings_data["transmitPort"];
                for key, value in data.items():
                    cmd.append("--" + shorten_packet_field(key))
                    cmd.append(str(value))

            # turn on debug
            cmd.append("--debug")
            cmd.append("True")

            #will raise CalledProcessError if sub process has non-zero exit code, instead of success message below
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")

            if is_json != -1:
                packet = get_packet_hex(output)
                if packet != '':
                    data["packet"] = packet

            if is_json == -1:
                return render_template('msg.html', message=Markup("Successfully sent DIFI packet.  <i>(To send more using the same field values, press 'Back' arrow in browser to return to the send page.)</i>"))
            else:
                return jsonify(data), 200

            #if redirect back to form, then store previous form in session
            #session["form_data"] = request.form
            #return redirect(request.url)
            #return redirect(request.referrer)


        #if not 'POST' (i.e. just regular 'GET')
        params = {}

        #if redirect back to form, then store previous form in session
        #form_data = session.get("form_data", None)
        #if form_data:
        #    params = form_data
        #    session.pop("form_data")

        #attempt to pre-fill target host/port in html page with host/port of flask and drx.py servers
        params["send_host"] = None if request.headers.get("Host") is None else request.headers.get("Host").split(':')[0]
        params["send_port"] = 4991
        if os.getenv("DIFI_RX_PORT"):
            params["send_port"] = os.getenv("DIFI_RX_PORT")
        return render_template('send_version_context.html', **params)

        #if redirect back to form, then store previous form in session
        #return render_template('send_version_context.html', form=params)
        #
        #in html page:
        #<input value="{{form["--cif0"]|default('00000002')}}"...

    except CalledProcessError as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))))
        else:
            return  jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))), 500
    except Exception as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure you entered an IP address and port and that all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500



@app.route('/web/v1/difi/send/signal-data', methods=['GET', 'POST'])
@app.route('/api/v1/difi/send/signal-data', methods=['POST'])
def send_signal_data_packets():

    """HTML web page used to send 'Signal Data' packets to a target IP address."""

    is_json = request.content_type.find("application/json") if request.content_type else False

    try:
        #if 'POST'
        if request.method == "POST":

            cmd = []
            cmd.append("python3")
            cmd.append("dds.py")

            if is_json == -1:
                for key,value in request.form.items():

                    if value is not None and value != "" and key.lower().startswith("--"):
                        #key is expected to have '--' on front,
                        #html elements named the same as dds.py script args
                        #even though is brittle in order to help make it
                        #easier to spot when missing or incorrect
                        cmd.append(key)
                        cmd.append(value)
            else:
                data = request.get_json();

                settings_data = get_settings()
                if settings_data["transmitEnabled"] == False:
                    return jsonify(error_code=400, message="Unable to submit packet while transmit is disabled."), 400
                if not "address" in data:
                    data["address"] = settings_data["transmitHost"];
                if not "port" in data:
                    data["port"] = settings_data["transmitPort"];
                for key, value in data.items():
                    cmd.append("--" + shorten_packet_field(key))
                    cmd.append(str(value))

            # turn on debug
            cmd.append("--debug")
            cmd.append("True")

            #will raise CalledProcessError if sub process has non-zero exit code, instead of success message below
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")

            if is_json != -1:
                packet = get_packet_hex(output)
                if packet != '':
                    data["packet"] = packet

            if is_json == -1:
                return render_template('msg.html', message=Markup("Successfully sent DIFI packet.  <i>(To send more using the same field values, press 'Back' arrow in browser to return to the send page.)</i>"))
            else:
                return jsonify(data), 200

            #if redirect back to form, then store previous form in session
            #session["form_data"] = request.form
            #return redirect(request.url)
            #return redirect(request.referrer)


        #if not 'POST' (i.e. just regular 'GET')
        params = {}

        #if redirect back to form, then store previous form in session
        #form_data = session.get("form_data", None)
        #if form_data:
        #    params = form_data
        #    session.pop("form_data")

        #attempt to pre-fill target host/port in html page with host/port of flask and drx.py servers
        params["send_host"] = None if request.headers.get("Host") is None else request.headers.get("Host").split(':')[0]
        params["send_port"] = 4991
        if os.getenv("DIFI_RX_PORT"):
            params["send_port"] = os.getenv("DIFI_RX_PORT")
        return render_template('send_signal_data.html', **params)

        #if redirect back to form, then store previous form in session
        #return render_template('send_signal_data.html', form=params)
        #
        #in html page:
        #<input value="{{form["--icc"]|default('0000')}}"...

    except CalledProcessError as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))))
        else:
            return  jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, highlight_bad_field_in_exception(e.stderr.decode(sys.getfilesystemencoding()), e))), 500
    except Exception as e:
        if is_json == -1:
            return render_template('msg.html', message=Markup("Failed to send packet. Make sure you entered an IP address and port and that all field values are within their valid ranges.  To try again, press 'Back' arrow in browser to return to the send page.<br><br>[%s] <br> %s" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500

####################
#api route handlers - OpenAPI endpoints (REST json / HTML GUI's)
####################
@app.route('/versions', methods=['GET'])
def get_versions():

    """Get versions of API supported."""

    try:
        data = {
            "versions": [
                "v1"
            ]
        }

        return jsonify(data), 200

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500

@app.route('/api/v1/difi/Info', methods=['GET'])
@app.route('/api/v1/Info', methods=['GET'])
@template_route('/web/v1/difi/Info', methods=['GET'])
def get_difi_openapi_info():

    """Gets information about the application.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        data = {
            "name": DIFI_NAME,
            "description": DIFI_DESCRIPTION,
            "version": get_version_info()
        }

        if is_template_route(request.url_rule):
            data["startTime"] = DIFI_START_TIME
            return render_template('info.html', info=data)
        else:
            return jsonify(data), 200

        #note: if don't use jsonify, these are manual ways to build response
        #d = '{"description":"DIFI packet decoder and sender.","name":"DIFI Validator","startTime":"02/16/2022 09:10:55 PM UTC","version":{"build":"0","major":1,"minor":0,"patch":0}}'
        #response = Response(response=d,
        #    status=200,
        #    mimetype="application/json")
        #return (response, 200)
        #
        #from flask import make_response
        #response = make_response(json.dumps(d))
        #response.headers['content-type'] = 'application/json'
        #return (response, 200)

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/Ready', methods=['GET'])
@app.route('/api/v1/Ready', methods=['GET'])
def get_difi_openapi_ready():

    """Gets whether the application is ready to be used."""

    try:
        return jsonify(ready=True), 200
    except Exception as e:
        return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/Health', methods=['GET'])
@template_route('/web/v1/difi/Health', methods=['GET'])
def get_difi_openapi_health():

    """Gets health of the system.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:
        for proc in psutil.process_iter():
            if "drx.py" in proc.cmdline():
                data = {
                    "status": "Running",
                    "createTime": datetime.fromtimestamp(proc.create_time(), tz=timezone.utc).isoformat(),
                    "subsystems": [{
                        "name": "drx",
                        "status": "Running",
                        "startTime": datetime.fromtimestamp(proc.create_time(), tz=timezone.utc).isoformat(),
                        "message": "UDP socket listener is listening for DIFI packets."
                        },
                        {
                        "name": "flask",
                        "status": "Running",
                        "startTime": DIFI_START_TIME,
                        "message": "Flask web server is running."
                        }]
                }
                if is_template_route(request.url_rule):
                    return render_template('health.html', info=data)
                else:
                    return jsonify(data), 200

        resp = {
            "status": "Stopped",
            "createTime": None,
            "subsystems": [{
                "name": "drx",
                "status": "Stopped",
                "startTime": None,
                "message": "UDP socket listener has stopped listening for DIFI packets."
                },
                {
                "name": "flask",
                "status": "Running",
                "startTime": DIFI_START_TIME,
                "message": "Flask web server is running."
                }]
        }
        if is_template_route(request.url_rule):
            return jsonify(resp), 200
        else:
            return render_template('health.html', info=resp)

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/Status', methods=['GET'])
@template_route('/web/v1/difi/Status', methods=['GET'])
def get_difi_openapi_status():

    """Gets application status.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    try:

        d = {}
        d["flask"] = [{
            "id": 1,
            "startTime": DIFI_START_TIME
        }]

        #get packet counts for streams
        streams = {}
        with os.scandir(path=DIFI_CACHE_HOME) as directory:
            for entry in directory:
                if entry.is_file():

                    #compliant files
                    if entry.name.startswith(DIFI_COMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        stream_id = entry.name.replace(DIFI_COMPLIANT_COUNT_FILE_PREFIX, "", 1)
                        stream_id = stream_id.replace(DIFI_FILE_EXTENSION, "", 1)
                        count = 0
                        updated = None
                        with open(entry, 'r', encoding="utf-8") as f:
                            buf = f.read()
                            if len(buf) > 0:
                                item = buf.split("#", 1)
                                count = int(item[0])
                                if len(item) > 1:
                                    updated = item[1]
                        if stream_id in streams:
                            streams[stream_id]["compliantPacketCount"] = count
                            streams[stream_id]["compliantUpdated"] = updated
                        else:
                            streams[stream_id] = {
                                "id": stream_id,
                                "compliantPacketCount": count,
                                "compliantUpdated": updated,
                                "noncompliantPacketCount": 0,
                                "noncompliantUpdated": None
                                }

                    #non-compliant files
                    if entry.name.startswith(DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        stream_id = entry.name.replace(DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, "", 1)
                        stream_id = stream_id.replace(DIFI_FILE_EXTENSION, "", 1)
                        count = 0
                        updated = None
                        with open(entry, 'r', encoding="utf-8") as f:
                            buf = f.read()
                            if len(buf) > 0:
                                item = buf.split("#", 1)
                                count = int(item[0])
                                if len(item) > 1:
                                    updated = item[1]
                        if stream_id in streams:
                            streams[stream_id]["noncompliantPacketCount"] = count
                            streams[stream_id]["noncompliantUpdated"] = updated
                        else:
                            streams[stream_id] = {
                                "id": stream_id,
                                "compliantPacketCount": 0,
                                "compliantUpdated": None,
                                "noncompliantPacketCount": count,
                                "noncompliantUpdated": updated
                                }

        #sort by stream id
        d["drxStreams"] = sorted(list(streams.values()), key=lambda stream_item: stream_item["id"])

        if is_template_route(request.url_rule):
            return render_template('status.html', streams=d["drxStreams"])
        else:
            return jsonify(d), 200

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/Settings', methods=['GET', 'PUT'])
@app.route('/api/v1/Settings', methods=['GET', 'PUT'])
@template_route('/web/v1/difi/Settings', methods=['GET'])
def get_difi_openapi_settings():

    """Gets or puts application settings.
    \n:Returns:
    \n* api route--> returns JSON document
    \n* web route--> returns HTML web page
    """

    settings_data = get_settings()
    receiveEnabled = settings_data["receiveEnabled"];
    transmitEnabled = settings_data["transmitEnabled"];
    transmitHost = settings_data["transmitHost"];
    transmitPort = settings_data["transmitPort"];

    try:
        if request.method == 'GET':

            #environment variables
            drx_port = os.getenv("DIFI_RX_PORT") if os.getenv("DIFI_RX_PORT") else None
            drx_mode = os.getenv("DIFI_RX_MODE") if os.getenv("DIFI_RX_MODE") else None
            drx_host = os.getenv("DIFI_RX_HOST") if os.getenv("DIFI_RX_HOST") else None
            flask_run_host = os.getenv("FLASK_RUN_HOST") if os.getenv("FLASK_RUN_HOST") else None
            flask_run_port = os.getenv("FLASK_RUN_PORT") if os.getenv("FLASK_RUN_PORT") else None

            #flask runtime
            url = urlparse(request.base_url)
            flask_runtime_address = url.hostname
            flask_runtime_port = url.port

            #drx runtime
            drx_runtime_address = None
            drx_runtime_port = None
            try:
                for proc in psutil.Process().parent().children():
                    if "drx.py" in proc.cmdline():
                        for cn in proc.connections():
                            drx_runtime_address = cn.laddr.ip
                            drx_runtime_port = cn.laddr.port
                            break
                        break
            except Exception:
                pass

            data = {
                "drx": {
                    "difiRxEnabled": receiveEnabled,
                    "difiRxPort": drx_port,
                    "difiRxMode": drx_mode,
                    "difiRxHost": drx_host,
                    "runtimeAddress": drx_runtime_address,
                    "runtimePort": drx_runtime_port
                    },
                "flask": {
                    "flaskRunHost": flask_run_host,
                    "flaskRunPort": flask_run_port,
                    "runtimeAddress": flask_runtime_address,
                    "runtimePort": flask_runtime_port
                    },
                "transmit": {
                    "difiTxEnabled": transmitEnabled,
                    "difiTxHost": transmitHost,
                    "difiTxPort": transmitPort
                    }
            }

            if is_template_route(request.url_rule):
                return render_template('settings.html', info=data)
            else:
                return jsonify(data), 200

        elif request.method == 'PUT':

            #save: this is just to test sending 'PUT'.
            #<button type="button" class="btn btn-primary" onclick="return test_put()">Test ajax PUT</button>
            #<script src="https://code.jquery.com/jquery-3.6.0.js"></script>
            #<script>
			#function test_put() {
			#	$.ajax({
			#		url: '/api/v1/difi/Settings',
			#		type: 'PUT',
			#		data: {'key1': "val1", "key2": "val2"},
			#		success: function(data) {
			#			alert("success= [" + data.error_code + "] " + data.message);
			#		},
			#		error: function(data) {
			#			alert("failure= [JSON] " + JSON.stringify(data.responseJSON) + "  [TEXT] " + data.responseText);
			#		}
			#		});
			#}
            #</script>
            #
            #for key,value in request.form.items():
            #    print("key=%s  val=%s" % (key, value))
            ##return type code 200, and will go to '.ajax.success function'
            #return jsonify(error_code=0, message="Modifying settings at runtime is not supported in this version."), 200
            ##return type code 503, and will go to '.ajax.error function'
            #return jsonify(error_code=503, message="Modifying settings at runtime is not supported in this version."), 503

            changed = 0

            data = request.get_json();
            if "drx" in data:
                if "difiRxEnabled" in data["drx"]:
                    settings_data["receiveEnabled"] = data["drx"]["difiRxEnabled"];
                    changed = 1
            if "transmit" in data:
                if "difiTxEnabled" in data["transmit"]:
                    settings_data["transmitEnabled"] = data["transmit"]["difiTxEnabled"];
                    changed = 1
                if "difiTxHost" in data["transmit"]:
                    settings_data["transmitHost"] = data["transmit"]["difiTxHost"];
                    changed = 1
                if "difiTxPort" in data["transmit"]:
                    settings_data["transmitPort"] = int(data["transmit"]["difiTxPort"])
                    changed = 1

            #accept changes but make no changes
            if changed == 1:
                put_settings(settings_data)
                return jsonify(error_code=200, message="Settings updated."), 200
            else:
                return jsonify(error_code=200, message="Modified settings are currently ignored."), 200
        else:
            raise Exception("request.method [" + request.method + "] not supported.")

    except Exception as e:
        if is_template_route(request.url_rule):
            return render_template('msg.html', message=Markup("[%s] %s\r\n" % (type(e).__name__, str(e))))
        else:
            return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


@app.route('/api/v1/difi/Operations/ResetStatistics', methods=['POST'])
def difi_openapi_operations_reset_statistics():

    """Resets all statistics for the application and returns status reply.  (Note: This operation will truncate the existing packet archive data files.)"""

    try:
        #truncate packet archive data files storing counts
        with os.scandir(path=DIFI_CACHE_HOME) as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)
                    elif entry.name.startswith(DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)

        return jsonify(operationStatus="Success"), 200
    except Exception as e:
        return jsonify(error_code=500, message="[%s] %s" % (type(e).__name__, str(e))), 500


# to run standalone flask server for debug, run using:  python3 webgui.py
if __name__ == '__main__':
    app.run('0.0.0.0', debug=True, port=5000)

# to run flask inside uwsgi server (like in a production environment) with flask app only visible as a unix socket for nginx acting as an 'application-gateway' server to communicate with,
# cd to home/difi/docker/input where webgui.py is and run:
#  sudo uwsgi --mount /=app:app --socket /tmp/difi.sock --chown-socket=www-data:www-data --uid=www-data --gid=www-data --chmod-socket=700 --master --manage-script-name --processes 5 --vacuum --die-on-term
# (notes about uwsgi args):
# / = sets url to root (this way flask url's will be the same, if was /application there would be additional /application prepending all existing flask url's)
# app = name of flask module file, without .py on end (i.e. webgui.py would be app)
# app = name of flask instance inside flask module file
# www-data = user and group that's created for nginx from over at top of nginx.conf file (/etc/nginx/nginx.conf)
# chown-socket = sets www-data to be owner of unix socket
# chmod-socket = modifies permissions on unix socket to 700 (7 gives owner r/w/x, 00 gives nothing to everyone else)


#@app.route('/status-compliant')
#def status_compliant():
#    p = subprocess.Popen(['tcpdump', '-r', 'difi-compliant.pcap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
#    res = p.communicate()
#    return res

#@app.route('/status-noncompliant')
#def status_noncompliant():
#    p = subprocess.Popen(['tcpdump', '-r', 'difi-noncompliant.pcap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
#    res = p.communicate()
#    return res

