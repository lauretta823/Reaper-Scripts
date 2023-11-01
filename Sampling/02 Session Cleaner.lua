-- Reascript Name : Session Cleaner
-- Description : Clear all the regions and the markers those begins with "/".
-- Version : 1.0

-- Split items function
local function splitItemsAtPosition(position)
    for j = 0, reaper.CountMediaItems(0)-1 do
        local item = reaper.GetMediaItem(0, j)
        local itemStart = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
        local itemEnd = itemStart + reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
        
        if position > itemStart and position < itemEnd then
            reaper.SplitMediaItem(item, position)
        end
    end
end

-- 1. Delete markers and regions starting with "/"
local i = 0
while i < reaper.CountProjectMarkers(0) do
    local _, isrgn, _, _, name, _ = reaper.EnumProjectMarkers(i)
    if name:sub(1,1) == "/" then
        reaper.DeleteProjectMarkerByIndex(0, i)
    else
        i = i + 1
    end
end

-- 2. Split all items at the beginning and end of each region
for i = 0, reaper.CountProjectMarkers(0)-1 do
    local _, isrgn, startPos, endPos = reaper.EnumProjectMarkers(i)
    if isrgn then
        splitItemsAtPosition(startPos)
        splitItemsAtPosition(endPos)
    end
end

-- 3. Delete items outside of any region
local itemsToDelete = {}
for j = 0, reaper.CountMediaItems(0)-1 do
    local item = reaper.GetMediaItem(0, j)
    local itemStart = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
    local itemEnd = itemStart + reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
    local isInRegion = false
    
    for i = 0, reaper.CountProjectMarkers(0)-1 do
        local _, isrgn, startPos, endPos = reaper.EnumProjectMarkers(i)
        if isrgn and not (itemEnd <= startPos or itemStart >= endPos) then
            isInRegion = true
            break
        end
    end
    
    if not isInRegion then
        table.insert(itemsToDelete, item)
    end
end

for _, item in ipairs(itemsToDelete) do
    reaper.DeleteTrackMediaItem(reaper.GetMediaItem_Track(item), item)
end

-- Update the graphical interface
reaper.UpdateArrange()

