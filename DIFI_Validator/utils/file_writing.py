import pprint
import os
from datetime import timezone, datetime
from typing import Union

from .difi_constants import *
from utils.custom_error_types import *
from utils.difi_data_packet_class import DifiDataPacket
from utils.difi_context_packet_class import DifiStandardContextPacket
from utils.difi_version_packet_class import DifiVersionContextPacket

DEBUG = False
JSON_AS_HEX = False  #converts applicable int fields in json doc to hex strings

def truncate_all_difi_files():
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


def write_noncompliant_to_file(e: NoncompliantDifiPacket):
    #TODO: in the future switch to write to kafka or database here instead...
    try:
        if type(e.difi_info.stream_id) is str:
            fname = "%s%s%s" % (DIFI_NONCOMPLIANT_FILE_PREFIX, e.difi_info.stream_id, DIFI_FILE_EXTENSION)
        else:
            fname = "%s%08x%s" % (DIFI_NONCOMPLIANT_FILE_PREFIX, e.difi_info.stream_id, DIFI_FILE_EXTENSION)

        with open(fname, 'w', encoding="utf-8") as f:

            #last_modified = datetime.fromtimestamp(os.stat(fname).st_mtime, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

            #add date timestamp to difi info object before writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            setattr(e.difi_info, "archive_date", now)

            f.write(e.difi_info.to_json()+"\r\n")
    except Exception:
        print("error writing to non-compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added entry to '%s' [%s]\r\n%s" % (fname, e, e.difi_info.to_json()))


def write_noncompliant_count_to_file(stream_id: Union[int,str]):
    #TODO: in the future switch to write to kafka or database here instead...
    try:
        if type(stream_id) is str:
            fname = "%s%s%s" % (DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
        else:
            fname = "%s%08x%s" % (DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
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


def write_compliant_to_file(packet: Union[DifiStandardContextPacket,DifiVersionContextPacket,DifiDataPacket]):
    if type(packet) not in (DifiStandardContextPacket, DifiVersionContextPacket, DifiDataPacket):
        print("packet type '%s' not allowed.\r\n" % (type(packet).__name__))
        return
    #TODO: in the future switch to write to kafka or database here instead...
    try:
        if type(packet) is DifiStandardContextPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_STANDARD_CONTEXT, packet.stream_id, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiVersionContextPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_VERSION_CONTEXT, packet.stream_id, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiDataPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_DATA, packet.stream_id, DIFI_FILE_EXTENSION)
        else:
            raise Exception("context packet type unknown")

        with open(fname, 'w', encoding="utf-8") as f:

            #add date timestamp to packet object before writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            setattr(packet, "archive_date", now)

            f.write(packet.to_json(JSON_AS_HEX)+"\r\n")
    except Exception as e:
        print("error writing to compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added last decoded '%s' to '%s'.\r\n" % (type(packet).__name__, fname))


def write_compliant_count_to_file(stream_id: int):
    #TODO: in the future switch to write to kafka or database here instead...
    try:
        fname = "%s%08x%s" % (DIFI_COMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
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
