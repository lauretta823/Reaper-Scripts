import os
from tkinter import filedialog
from tkinter import Tk
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

def parse_filename(filename):
    parts = filename.rstrip('.wav').split('_')
    micro = parts[0]
    note = parts[1] if len(parts) > 1 else None
    velocity = parts[2] if len(parts) > 2 else "127"
    round_robin = parts[3] if len(parts) > 3 else "RR1"
    return micro, note, velocity, round_robin

def generate_dspreset_file(source_folder, destination_folder, library_name):
    decent_sampler = Element("DecentSampler", minVersion="1.0.0", title=library_name)
    ui = SubElement(decent_sampler, "ui", width="1000", height="500", bgImage="Images/background.jpg")
    tab = SubElement(ui, "tab", name="main")
    groups = SubElement(decent_sampler, "groups")
    files_by_micro = {}

    for filename in os.listdir(source_folder):
        if filename.endswith(".wav"):
            micro, note, velocity, round_robin = parse_filename(filename)
            if micro not in files_by_micro:
                files_by_micro[micro] = []
            files_by_micro[micro].append((filename, note, velocity, round_robin))

    ui_width = 1000
    y_position = 30
    knob_width = 110

    num_micros = len(files_by_micro)
    knob_spacing = ui_width // (num_micros + 1)

    for idx, (micro, files) in enumerate(files_by_micro.items()):   
        x_base = knob_spacing * (idx + 1) - knob_width // 2
        
        labeled_knob = SubElement(tab, "labeled-knob", x=str(x_base), y=str(y_position), width="110", 
                              textSize="18", textColor="AA000000", trackForegroundColor="CC000000", 
                              trackBackgroundColor="66999999", label=f"Volume {micro}", 
                              type="float", minValue="0.0", maxValue="1.0", value="1.0")
        binding = SubElement(labeled_knob, "binding", type="amp", level="group", position=str(idx), 
                         parameter="AMP_VOLUME", translation="linear", 
                         translationOutputMin="0", translationOutputMax="1.0")
        
        y_adsr = y_position + 110
        adsr_parameters = [("attack", "ENV_ATTACK", "0.0", "10.0", "6.0"), 
                           ("decay", "ENV_DECAY", "0.0", "25.0", "0.0"), 
                           ("sustain", "ENV_SUSTAIN", "0.0", "1.0", "0.87"), 
                           ("release", "ENV_RELEASE", "0.0", "25.0", "15.0")]
        total_adsr_width = 4 * 10 + 3 * 15
        x_base_adjusted = x_base - total_adsr_width // 2 + knob_width // 2 

        for i, (param, env_param, min_val, max_val, default_val) in enumerate(adsr_parameters):
            x_position = x_base_adjusted + i * 25
            label = SubElement(tab, "label", x=str(x_position), y=str(y_adsr), width="15", height="15", 
                            text=param[0].upper(), textColor="AA000000", textSize="15")
            control = SubElement(tab, "control", x=str(x_position), y=str(y_adsr + 20), width="15", height="80", 
                                parameterName=param, style="linear_bar_vertical", type="float", 
                                minValue=min_val, maxValue=max_val, value=default_val, 
                                trackForegroundColor="CC000000", trackBackgroundColor="66999999")
            binding = SubElement(control, "binding", type="amp", level="group", position=str(idx), 
                                parameter=env_param, translation="linear", 
                                translationOutputMin="0", translationOutputMax="1.0")
            
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
                sample_file_path = os.path.join('Samples', filename)
                sample = SubElement(group, "sample", path=sample_file_path, rootNote=note, loNote=note, hiNote=note, loVel=str(lo_vel), hiVel=str(hi_vel))
                if round_robin:
                    sample.set("seqPosition", round_robin.replace('RR', ''))

    dspreset_file = os.path.join(destination_folder, f"{library_name}.dspreset")
    tree = ElementTree(decent_sampler)
    xml_str = minidom.parseString(tostring(decent_sampler)).toprettyxml(indent="  ")
    with open(dspreset_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

    # Create DSLibraryInfo XML file
    library_info = Element("DSLibraryInfo", name=library_name, productId="945455", version="1.1.0")
    library_info_file = os.path.join(destination_folder, "DSLibraryInfo.xml")
    library_info_tree = ElementTree(library_info)
    xml_str = minidom.parseString(tostring(library_info)).toprettyxml(indent="  ")
    with open(library_info_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    original_source_folder = filedialog.askdirectory(title="Select the folder to process")

    # Create 'Samples' folder inside the original source folder
    samples_folder = os.path.join(original_source_folder, 'Samples')
    if not os.path.exists(samples_folder):
        os.makedirs(samples_folder)

    # Create 'Images' folder inside the original source folder
    images_folder = os.path.join(original_source_folder, 'Images')
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    # Move .wav files to the 'Samples' folder
    for file in os.listdir(original_source_folder):
        if file.endswith('.wav'):
            os.rename(os.path.join(original_source_folder, file), os.path.join(samples_folder, file))

    if original_source_folder:
        library_name = input("Enter the name of the library: ")
        # Generate .dspreset and DSLibraryInfo.xml in the original source folder
        generate_dspreset_file(samples_folder, original_source_folder, library_name)

    input("Press Enter to exit...")
