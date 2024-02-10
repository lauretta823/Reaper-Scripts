# Description : Create toggle actions from parameters that can be used in Reaper's toolbar.
# Version : 1.0

def parse_params_from_input(input_text):
    """Parse the pasted input into a list of (index, name) tuples."""
    params = []
    for line in input_text.strip().split('\n'):
        if not line.startswith("Param index:"):
            continue
        parts = line.split(',')
        index_part, name_part = parts[0], parts[1]
        index = int(index_part.split(':')[1].strip())
        name = name_part.split(':')[1].strip()
        params.append((index, name))
    return params

def generate_lua_scripts(track_num, plugin_name, params):
    for param_index, param_name in params:
        script_content = f"""-- Generated Lua Script to toggle parameter
local track_num = {track_num}
local plugin_name_part = "{plugin_name}"
local param_index = {param_index}

-- Retrieve action context
_, _, sectionID, cmdID, _, _, _ = reaper.get_action_context()

-- Function to get the index of the plugin on the track
function get_plugin_idx(track)
    local fx_count = reaper.TrackFX_GetCount(track)
    for fx_idx = 0, fx_count - 1 do
        local ret, fx_name = reaper.TrackFX_GetFXName(track, fx_idx, "")
        if string.find(fx_name, plugin_name_part) then
            return fx_idx
        end
    end
    return -1 -- Plugin not found
end

-- Function to get the current toggle state of the parameter
function getCurrentParamToggleState(track, plugin_idx, param_index)
    local param_value = reaper.TrackFX_GetParamNormalized(track, plugin_idx, param_index)
    return param_value >= 0.5 and "1" or "0" -- Consider 0.5 as the threshold for toggle state
end

-- Function to toggle the plugin parameter
function togglePluginParameter(track, plugin_idx, param_index, expectedState)
    local currentState = getCurrentParamToggleState(track, plugin_idx, param_index)
    if currentState ~= expectedState then
        local newValue = currentState == "0" and 1 or 0
        reaper.TrackFX_SetParamNormalized(track, plugin_idx, param_index, newValue)
    end
end

-- Main execution starts here
local track = reaper.GetTrack(0, track_num - 1)
local plugin_idx = get_plugin_idx(track)
if plugin_idx ~= -1 then
    -- Determine the expected state based on the toolbar button state
    local expectedState = reaper.GetToggleCommandStateEx(sectionID, cmdID) == 1 and "0" or "1"
    togglePluginParameter(track, plugin_idx, param_index, expectedState)
    -- Update the toolbar button state to reflect the new state of the parameter
    reaper.SetToggleCommandState(sectionID, cmdID, expectedState == "1" and 1 or 0)
    reaper.RefreshToolbar2(sectionID, cmdID)
else
    reaper.ShowMessageBox("Plugin part of name '" .. plugin_name_part .. "' not found on track " .. track_num, "Error", 0)
end

-- No need to use defer for a toggle action

-- Cleanup function not needed for toggle action since it's stateful
"""
        script_name = f"FX_Switch_{track_num}_{plugin_name}_{param_name.replace(' ', '_')}.lua"
        with open(script_name, "w") as script_file:
            script_file.write(script_content)
        print(f"Generated Lua script: {script_name}")

def main():
    track_num = input("Enter the track number where the plugin is placed: ")
    plugin_name = input("Enter part of the plugin name: ")
    print("Paste the parameters list, then type 'end' on a new line and press Enter:")
    input_lines = []
    while True:
        line = input()
        if line == 'end':
            break
        input_lines.append(line)
    input_text = '\n'.join(input_lines)
    params = parse_params_from_input(input_text)
    generate_lua_scripts(track_num, plugin_name, params)

if __name__ == "__main__":
    main()