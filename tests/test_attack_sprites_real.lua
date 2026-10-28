package.path='./?.lua;./?/init.lua;'..package.path
local hero=require('src.playtest').findHero(dofile('cache/animations.lua'))
local atlas=dofile('cache/atlases.lua')
local resolve=require('src.sprite_resolver')
local pose=require('src.pose')
local A=require('src.attack_preview')
local idx=resolve.index(atlas)
local resolved=0
for i=1,3 do for dir=0,4 do
    local s=A.new(hero,30)
    assert(A.begin(s,i,dir))
    local movement=A.sample(s)
    for _,node in ipairs(pose.evaluate(hero.armatures[1],movement,0,true,true)) do
        local di=node.display_index
        local label=di and di>=0 and node.bone.displays and node.bone.displays[di+1]
        if label and label~='' then
            local found=resolve.find(idx,hero,label)
            assert(found and found.atlas and found.frame,'Sprite ausente: '..label)
            resolved=resolved+1
        end
    end
end end
assert(resolved>20)
print('F20 sprites reais de ataque OK '..resolved)
