-- Reascript Name : Loops Creator.lua
-- Description : Create a seamless loop on each sample. 
-- Version : 1.0

-- Get the length of the time selection
start_time, end_time = reaper.GetSet_LoopTimeRange2(0, false, false, 0, 0, false)
time_selection_length = end_time - start_time
-- Get the end position of the first region
retval, isrgn, pos, rgnend, name, markrgnindexnumber = reaper.EnumProjectMarkers3(0, 0)
if retval == 1 and isrgn then
    first_region_end = rgnend
else
    first_region_end = 0
end

-- Calculate the value of endofloop_to_endofregion
endofloop_to_endofregion = first_region_end - end_time


function Msg(msg)
    reaper.ShowConsoleMsg(tostring(msg) .. "\n")
end

function Move_items()
    first_item = reaper.GetSelectedMediaItem(0,0)

    if first_item ~= nil then
        start_looptime, end_looptime = reaper.GetSet_LoopTimeRange2(0, false, false, 0, 0, false )
        start_first_item = reaper.GetMediaItemInfo_Value(first_item, "D_POSITION")
        length_first_item = reaper.GetMediaItemInfo_Value(first_item, "D_LENGTH") 

        count_sel_item =  reaper.CountSelectedMediaItems(0)
        Msg("Selected Items = "..count_sel_item)
        
        selected_items_details = {}

        for i = 0, count_sel_item - 1 do
            item = reaper.GetSelectedMediaItem(0, i)
            local item_position = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
            local item_length = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
            
            table.insert(selected_items_details, {item = item, position = item_position, length = item_length})
        end

        for i, item_details in ipairs(selected_items_details) do
            local new_position = item_details.position + (i-1) * time_selection_length
            reaper.SetMediaItemInfo_Value(item_details.item, "D_POSITION", new_position)
        end
    end
end

function Move_regions()
    local i = 0
    local region_idx = 0
    local regions = {}

    while true do
        local retval, isrgn, pos, rgnend, name, markrgnindexnumber = reaper.EnumProjectMarkers3(0, i)
        if retval == 0 then
            break
        end
        if isrgn then
            table.insert(regions, {index = markrgnindexnumber, pos = pos, rgnend = rgnend, name = name})
            region_idx = region_idx + 1
        end
        i = i + 1
    end

    for i, region in ipairs(regions) do
        local new_pos = region.pos + (i-1) * time_selection_length
        local new_end = region.rgnend + i * time_selection_length - (endofloop_to_endofregion + 0.5 * time_selection_length)
        reaper.SetProjectMarker3(0, region.index, true, new_pos, new_end, region.name, 0)
    end
end

function Loop_Creator()
    first_item = reaper.GetSelectedMediaItem(0,0)

    if first_item ~= nil then
        -- Get the current value of the "Create automatic fade-in/fade-out for new items and when splitting" option
        local auto_fade_state = reaper.GetToggleCommandStateEx(0, 41194)
        
        -- Disable the "Create automatic fade-in/fade-out for new items and when splitting" option
        if auto_fade_state == 1 then
            reaper.Main_OnCommand(41194, 0)
        end
        
        start_looptime, end_looptime = reaper.GetSet_LoopTimeRange2(0, false, false, 0, 0, false )
        start_first_item = reaper.GetMediaItemInfo_Value(first_item, "D_POSITION")
        length_first_item = reaper.GetMediaItemInfo_Value(first_item, "D_LENGTH")
        cut_first = (start_looptime - start_first_item)
        cut_last = (end_looptime - start_first_item)
        length_middle = cut_last - cut_first

        Msg("cut first = " ..cut_first)
        Msg("cut last = " ..cut_last)
        Msg("length middle = " ..length_middle)
  
        count_sel_item =  reaper.CountSelectedMediaItems(0)
        Msg("Selected Items = "..count_sel_item)
    
        selected_items = {}

        for i = 0, count_sel_item - 1 do
            item = reaper.GetSelectedMediaItem(0, i)
            table.insert(selected_items, item)
        end
    
        for i, item in ipairs(selected_items) do
            Msg("i = " ..i)
            start_item = reaper.GetMediaItemInfo_Value(item, "D_POSITION")

            reaper.SplitMediaItem(item, start_item + cut_last)
            reaper.SplitMediaItem(item, start_item + cut_first + 0.5 * length_middle)
            reaper.SplitMediaItem(item, start_item + cut_first)
        end
    
        cut_items = {}
        for i = 0, reaper.CountMediaItems(0) - 1 do
            item = reaper.GetMediaItem(0, i)
            table.insert(cut_items, item)
        end
    
        for i = 1, #cut_items, 4 do
            if cut_items[i] and cut_items[i+1] and cut_items[i+2] and cut_items[i+3] then
                length_item1 = reaper.GetMediaItemInfo_Value(cut_items[i], "D_LENGTH")
                length_item2 = reaper.GetMediaItemInfo_Value(cut_items[i+1], "D_LENGTH")
                length_item3 = reaper.GetMediaItemInfo_Value(cut_items[i+2], "D_LENGTH")
                length_item4 = reaper.GetMediaItemInfo_Value(cut_items[i+3], "D_LENGTH")

                start_item = reaper.GetMediaItemInfo_Value(cut_items[i], "D_POSITION")

                reaper.SetMediaItemInfo_Value(cut_items[i+3], "D_POSITION", start_item + length_item1 + length_item2 + length_item3 + length_item2 + length_item3)
                
                start_part4 = start_item + length_item1 + length_item2 + length_item3 - 0.25 * length_middle
                end_part4 = start_item + length_item1 + length_item2 + length_item3 + length_item2 + length_item3 + length_item4

                Msg("start_part4 = " ..start_part4)
                Msg("end_part4 = " ..end_part4)

                reaper.BR_SetItemEdges(cut_items[i+3], start_part4, end_part4)

                start_item3 = reaper.GetMediaItemInfo_Value(cut_items[i+2], "D_POSITION")
                reaper.AddProjectMarker2(0, true, start_item3, start_item3 + length_middle, "#LOOP", -1, 0)
            else
                Msg("Skipping group of 4 items starting at index " .. i .. " because not all items exist.")
            end
        end
        
        -- Restore the original state of the "Create automatic fade-in/fade-out for new items and when splitting" option
        if auto_fade_state == 1 then
            reaper.Main_OnCommand(41194, 0)
        end
    else 
        Msg("No Item selected")
    end

    -- Update the graphical interface
    reaper.UpdateArrange()
end

-- Start the undo block
reaper.Undo_BeginBlock()

-- Run the functions
reaper.ShowConsoleMsg("")
Move_items()
Move_regions()
Loop_Creator()

-- End the undo block and allow to undo the whole script with one undo action
reaper.Undo_EndBlock("Run script with multiple actions", -1)

