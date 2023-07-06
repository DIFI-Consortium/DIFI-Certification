import pprint
import os
from datetime import timezone, datetime
from typing import Union
import json

from difi_utils.difi_constants import *
from difi_utils.custom_error_types import *
from difi_utils.difi_data_packet_class import DifiDataPacket
from difi_utils.difi_context_packet_class import DifiStandardContextPacket
from difi_utils.difi_version_packet_class import DifiVersionContextPacket

DEBUG = False
JSON_AS_HEX = False  #converts applicable int fields in json doc to hex strings

def append_item_to_json_file(fname, entry):
    #new_item = entry.to_json(hex_values=True) # does json dumps, using hex for the fields that are better in hex
    new_item = entry.to_json()

    if not os.path.isfile(fname):
        with open(fname, mode='w', encoding="utf-8") as f:
            f.write('[\n' + new_item + '\n]')
    else:
        # Remove last line of file, which should contain the closing brackets
        with open(fname, "r+", encoding = "utf-8") as f:
            f.seek(0, os.SEEK_END) # Move the pointer (similar to a cursor in a text editor) to the end of the file
            pos = f.tell() - 1 # skip to the very last character in the file 
            while pos > 0 and f.read(1) != "\n":
                pos -= 1
                f.seek(pos, os.SEEK_SET)
            # delete all characters ahead of this point
            f.seek(pos, os.SEEK_SET)
            f.truncate()

            # now add the new entry
            f.write(',\n' + new_item + '\n]')

def write_compliant_to_file(packet: Union[DifiStandardContextPacket, DifiVersionContextPacket, DifiDataPacket]):
    if type(packet) not in (DifiStandardContextPacket, DifiVersionContextPacket, DifiDataPacket):
        print("packet type '%s' not allowed.\r\n" % (type(packet).__name__))
        return
    try:
        if type(packet) is DifiStandardContextPacket:
            fname = "%s%s%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_STANDARD_CONTEXT, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiVersionContextPacket:
            fname = "%s%s%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_VERSION_CONTEXT, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiDataPacket:
            fname = "%s%s%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_DATA, DIFI_FILE_EXTENSION)
        else:
            raise Exception("context packet type unknown")

        
        #add date timestamp to packet object before writing to file
        now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
        setattr(packet, "archive_date", now)

        append_item_to_json_file(fname, packet)

    except Exception as e:
        print("error writing to compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added last decoded '%s' to '%s'.\r\n" % (type(packet).__name__, fname))


def write_compliant_count_to_file():
    try:
        fname = "%s%s" % (DIFI_COMPLIANT_COUNT_FILE_PREFIX, DIFI_FILE_EXTENSION)
        with open(fname, 'a+', encoding="utf-8") as f:
            f.seek(0)
            c = 0
            buf = f.read()
            if buf:
                entry = buf.split("#", 1)
                c = int(entry[0])
            c = c + 1
            #add date timestamp when writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            out = "%s#%s" % (str(c), now)
            f.seek(0)
            f.truncate()
            f.write(out)
    except Exception as e:
        print("error writing to compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("incremented entry in '%s'.\r\n" % (fname))

def write_noncompliant_to_file(e: NoncompliantDifiPacket):
    try:
        fname = "%s%s" % (DIFI_NONCOMPLIANT_FILE_PREFIX, DIFI_FILE_EXTENSION)

        #last_modified = datetime.fromtimestamp(os.stat(fname).st_mtime, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

        #add date timestamp to difi info object before writing to file
        now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
        setattr(e.difi_info, "archive_date", now)
        append_item_to_json_file(fname, e.difi_info)

    except Exception as e:
        print("error writing to non-compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added entry to '%s' [%s]\r\n%s" % (fname, e, e.difi_info.to_json()))


def write_noncompliant_count_to_file():
    try:
        fname = "%s%s" % (DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, DIFI_FILE_EXTENSION)
        with open(fname, 'a+', encoding="utf-8") as f:
            f.seek(0)
            c = 0
            buf = f.read()
            if buf:
                entry = buf.split("#", 1)
                c = int(entry[0])
            c = c + 1
            #add date timestamp when writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            out = "%s#%s" % (str(c), now)
            f.seek(0)
            f.truncate()
            f.write(out)
    except Exception as e:
        print("error writing to non-compliant count file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("incremented entry in '%s'.\r\n" % (fname))


def clear_all_difi_files():
    try:
        with os.scandir() as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)
                    elif entry.name.startswith(DIFI_NONCOMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)
    except Exception as e:
        print("error truncating DIFI output files -->")
        pprint.pprint(e)

    if DEBUG: print("truncated all difi output files...")


def delete_all_difi_files():
    try:
        with os.scandir() as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.remove(entry.path)
                    elif entry.name.startswith(DIFI_NONCOMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.remove(entry.path)
    except Exception as e:
        print("error deleting DIFI output files -->")
        pprint.pprint(e)

    if DEBUG: print("deleted all difi output files...")