# Name: Reaper_To_DS
# Function: Create a DecentSampler library from Reaper export samples
# Version: 1.0

import os
from tkinter import filedialog
from tkinter import Tk
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

def parse_filename(filename):
    parts = filename.rstrip('.wav').split('_')
    micro = parts[0]
    note = parts[1] if len(parts) > 1 else None
    velocity = parts[2] if len(parts) > 2 else None
    round_robin = parts[3] if len(parts) > 3 else None
    return micro, note, velocity, round_robin

def generate_dspreset_file(source_folder, library_name):
    decent_sampler = Element("DecentSampler", minVersion="1.0.0", title=library_name)
    groups = SubElement(decent_sampler, "groups")
    files_by_micro = {}
    for filename in os.listdir(source_folder):
        if filename.endswith(".wav"):
            micro, note, velocity, round_robin = parse_filename(filename)
            if micro not in files_by_micro:
                files_by_micro[micro] = []
            files_by_micro[micro].append((filename, note, velocity, round_robin))

    for micro, files in files_by_micro.items():
        group = SubElement(groups, "group", tags=micro, silencedByTags=micro)
        rr_groups = {}
        velocities_by_note = {}
        for filename, note, velocity, round_robin in files:
            if note not in rr_groups:
                rr_groups[note] = []
                velocities_by_note[note] = set()
            rr_groups[note].append((filename, velocity, round_robin))
            velocities_by_note[note].add(int(velocity))
        
        for note, velocities in velocities_by_note.items():
            sorted_velocities = sorted(list(velocities))
            ranges = []
            lo = 0
            for hi in sorted_velocities:
                ranges.append((lo, hi))
                lo = hi + 1
            velocities_by_note[note] = ranges

        for note, rr_files in rr_groups.items():
            if len(rr_files) > 1:
                group.set("seqMode", "random")
            for idx, (filename, velocity, round_robin) in enumerate(rr_files):
                lo_vel, hi_vel = next((r for r in velocities_by_note[note] if r[1] == int(velocity)), (0, 127))
                sample_file_path = os.path.relpath(os.path.join(source_folder, filename), source_folder)
                sample = SubElement(group, "sample", path=sample_file_path, rootNote=note, loNote=note, hiNote=note, loVel=str(lo_vel), hiVel=str(hi_vel))
                if round_robin:
                    sample.set("seqPosition", round_robin.replace('RR', ''))

    dspreset_file = os.path.join(source_folder, f"{library_name}.dspreset")
    tree = ElementTree(decent_sampler)
    xml_str = minidom.parseString(tostring(decent_sampler)).toprettyxml(indent="  ")
    with open(dspreset_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

    # Create DSLibraryInfo XML file
    library_info = Element("DSLibraryInfo", name=library_name, productId="945455", version="1.1.0")
    library_info_file = os.path.join(source_folder, "DSLibraryInfo.xml")
    library_info_tree = ElementTree(library_info)
    xml_str = minidom.parseString(tostring(library_info)).toprettyxml(indent="  ")
    with open(library_info_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    source_folder = filedialog.askdirectory(title="Select the folder to process")
    if source_folder:
        library_name = input("Enter the name of the library: ")
        generate_dspreset_file(source_folder, library_name)
    input("Press Enter to exit...")
