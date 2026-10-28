package.path='./?.lua;./?/init.lua;'..package.path
local P=require('src.playtest')
local anim=dofile('cache/animations.lua')
local atlas=dofile('cache/atlases.lua')
local maps=dofile('cache/maps.lua')
local hero=P.findHero(anim)
assert(hero and hero.path=='character/babarian/babarian.bexportjson')
local resolver=require('src.sprite_resolver')
local pose=require('src.pose')
local sprites=resolver.index(atlas)
for _,walk in ipairs({false,true}) do
    local move=P.movement(hero,walk,0)
    assert(move and move.duration>=40)
    local count=0
    for _,node in ipairs(pose.evaluate(hero.armatures[1],move,0,true,true)) do
        local di=node.display_index
        local display=di and di>=0 and node.bone.displays and node.bone.displays[di+1]
        if display then
            local found=resolver.find(sprites,hero,display)
            assert(found and found.frame and found.atlas.image, 'sprite real sem correspondência: '..display)
            count=count+1
        end
    end
    assert(count>=3)
end
local m
for _,map in ipairs(maps) do if map.name=='petisland_01' then m=map end end
assert(m and m.width==16 and m.height==10)
print('F18 integração animação original e mapa real OK')