#!/usr/local/bin/python3 -Es
import argparse
import fileinput
import os
import dateutil.parser as dateparser
import xml.etree.ElementTree as ET

__author__ = 'Stefan Weiberg'
__license__ = 'EUPLv2'
__version__ = '0.0.1'
__maintainer__ = 'Stefan Weiberg'
__email__ = 'sweiberg@suse.com'
__status__ = 'Development'

desc = "tool to merge tcx files from coxswain with HR information from a gpx export from HealthFit"
parser = argparse.ArgumentParser()

parser.add_argument("-t", dest="tcx", type=str, required=True,
                    help="tcx file from coxswain")
parser.add_argument("-g", dest="gpx", type=str, required=True,
                    help="gpx file from HealthFit")

args = parser.parse_args()

tcx_file = args.tcx
gpx_file = args.gpx

ns_gpx = {"ns": "http://www.topografix.com/GPX/1/1",
          "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"}
ns_tcx = {"ns": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

if __name__ == "__main__":
    try:
        gpx_root = ET.parse(gpx_file).getroot()
        tcx_tree = ET.parse(tcx_file)
        tcx_root = tcx_tree.getroot()

        lap = tcx_root.find("ns:Activities", ns_tcx).find("ns:Activity", ns_tcx).find("ns:Lap", ns_tcx)
        track = lap.find("ns:Track", ns_tcx)

        hr_data = {}
        for trkseg in gpx_root.find("ns:trk", ns_gpx).findall("ns:trkseg", ns_gpx):
            for trkpt in trkseg.findall("ns:trkpt", ns_gpx):
                gpx_time = trkpt.find("ns:time", ns_gpx).text
                gpxtpx = trkpt.find("ns:extensions", ns_gpx).find("gpxtpx:TrackPointExtension", ns_gpx)
                hr = gpxtpx.find("gpxtpx:hr", ns_gpx)
                hr_data.update({dateparser.isoparse(gpx_time).replace(microsecond=0): hr.text})

        hr_target = {}
        for trackpoint in track.findall("ns:Trackpoint", ns_tcx):
            tcx_time = trackpoint.find("ns:Time", ns_tcx).text
            heart_rate_bpm = trackpoint.find("ns:HeartRateBpm", ns_tcx).find("ns:Value", ns_tcx)
            hr_target.update({dateparser.isoparse(tcx_time).replace(microsecond=0): heart_rate_bpm})

        j = 0
        for i, input_timestamp in enumerate(hr_data, start=0):    
            for j, target_timestamp in enumerate(hr_target, start=j):
                if input_timestamp <= target_timestamp:
                    try:
                        if list(hr_data)[i+1] > target_timestamp:
                            hr_target[target_timestamp].text = hr_data[input_timestamp]
                        else:
                            break
                    except IndexError:
                        hr_target[target_timestamp].text = hr_data[input_timestamp]
                        break
        
        ET.register_namespace('',"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        ET.register_namespace('TPX',"http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        tcx_tree.write('output.tcx', encoding='utf8')

        with open('output.tcx', 'r') as file :
            filedata = file.read()

        filedata = filedata.replace("TPX:TPX", 'TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2"')
        filedata = filedata.replace("TPX:", "")
        filedata = filedata.replace('</TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">', "</TPX>")

        with open('output.tcx', 'w') as file:
            file.write(filedata)
    except Exception as error:
        print('ERROR', error)
    pass