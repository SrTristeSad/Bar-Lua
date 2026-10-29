-- Candidate actors from recovered BarbarQ bExport animation catalog.
-- This is a visual-compatibility filter, NOT classification of original enemy roles.
local Catalog={}
local function movement(asset,name)
    for _,animation in ipairs((asset and asset.animations) or {}) do
        for _,move in ipairs(animation.movements or {}) do
            if move.name==name and type(move.duration)=='number' and move.duration>0 then
                return move
            end
        end
    end
end
function Catalog.usable(asset, index)
    if type(asset)~='table' or type(asset.path)~='string' then return false end
    if not asset.path:lower():match('^character/') then return false end
    if asset.path=='character/babarian/babarian.bexportjson' then return false end
    local arm=asset.armatures and asset.armatures[1]
    if type(arm)~='table' or type(arm.bones)~='table' then return false end
    if not movement(asset,'stand_0') or not movement(asset,'walk_0') then return false end
    local visible=0
    for _,bone in ipairs(arm.bones) do
        for _,label in ipairs(bone.displays or {}) do
            if type(label)=='string' and label~='' then
                local sprite=index and require('src.sprite_resolver').find(index,asset,label)
                if sprite and sprite.frame and sprite.atlas then
                    visible=visible+1
                    break
                end
            end
        end
        if visible>0 then break end
    end
    return visible>0
end
function Catalog.select(animations,index,limit)
    limit=limit or 12
    local chosen={}
    for _,asset in ipairs(animations or {}) do
        if Catalog.usable(asset,index) then chosen[#chosen+1]=asset end
    end
    table.sort(chosen,function(a,b)return a.path<b.path end)
    -- Choose a spread across the catalog, rather than the first directory only.
    if #chosen<=limit then return chosen end
    local spread={}
    for i=1,limit do
        local j=1+math.floor((i-1)*(#chosen-1)/math.max(1,limit-1))
        spread[#spread+1]=chosen[j]
    end
    return spread
end
return Catalog
