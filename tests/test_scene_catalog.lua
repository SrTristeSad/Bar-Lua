package.path='./?.lua;./?/init.lua;'..package.path
local L=require('src.scene_layout')
local R=require('src.scene_resources')
local atlases=dofile('cache/atlases.lua')
local scenes=dofile('cache/scenes.lua')
local index=R.build(atlases,{})
local nodes,found,missing=0,0,0
for _,scene in ipairs(scenes) do
    local flat=L.flatten(scene)
    assert(#flat==scene.node_count,scene.name..': hierarquia perdeu nós')
    nodes=nodes+#flat
    for _,entry in ipairs(flat) do
        local resource=entry.node.resource
        if resource then
            if R.find(index,resource) then found=found+1
            else missing=missing+1 end
        end
    end
end
assert(#scenes==560 and nodes==26612)
print('Catálogo real:',#scenes,'cenas,',nodes,'nós,',found,'atlas,',missing,'não-atlas')
