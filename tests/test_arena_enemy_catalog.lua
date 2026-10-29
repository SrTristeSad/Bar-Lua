package.path='./?.lua;./?/init.lua;'..package.path
local Index=require('src.sprite_resolver')
local Catalog=require('src.arena_enemy_catalog')
local Art=require('src.arena_original_art')
local function asset(path,display)
    return {
        path=path,atlas_files={'sprites.plist'},
        armatures={{bones={{name='root',initial_display=0,displays={display}}}}},
        animations={{movements={
            {name='stand_0',duration=30,tracks={}},
            {name='walk_0',duration=30,tracks={}},
            {name='attack1_0',duration=32,tracks={}}
        }}}
    }
end
local hero=asset('character/babarian/babarian.bexportjson','player')
local frog=asset('character/z_frog/frog.bexportjson','frog0')
local fox=asset('character/a_fox/fox.bexportjson','fox0')
local invalid=asset('effects/sparks/sparks.bexportjson','spark0')
local incomplete=asset('character/ghost/ghost.bexportjson','ghost0')
incomplete.animations[1].movements[2].name='dance_0'
local atlases={}
for _,info in ipairs({
    {path='character/a_fox/sprites.bplist',display='fox0'},
    {path='character/z_frog/sprites.bplist',display='frog0'},
    {path='character/babarian/sprites.bplist',display='player'},
    {path='effects/sparks/sprites.bplist',display='spark0'}
}) do
    atlases[#atlases+1]={path=info.path,image=info.display..'.png',
        frames={{name=info.display,x=0,y=0,w=16,h=16,source_w=16,source_h=16}}}
end
local source={frog,hero,invalid,incomplete,fox}
local idx=Index.index(atlases)
assert(not Catalog.usable(hero,idx))
assert(not Catalog.usable(invalid,idx))
assert(not Catalog.usable(incomplete,idx))
assert(Catalog.usable(frog,idx) and Catalog.usable(fox,idx))
local choices=Catalog.select(source,idx)
assert(#choices==2)
assert(choices[1].path==fox.path and choices[2].path==frog.path)
local o=Art.prepare({},source,atlases)
assert(#o.enemyAssets==2)
local picked={}
love={
    graphics={
        newImage=function(path)
            picked[#picked+1]=path
            return {getWidth=function()return 32 end,
                    getHeight=function()return 32 end,
                    getDimensions=function()return 32,32 end,
                    setFilter=function()end}
        end,
        newQuad=function()return {} end,
        setColor=function()end,draw=function()end,
        push=function()end,pop=function()end,
        translate=function()end,scale=function()end,applyTransform=function()end,
    },
    math={newTransform=function()return {setMatrix=function()end} end}
}
local a={x=100,y=100,faceX=1,faceY=0,walking=true,skin=1}
assert(Art.drawHero(o,a,0,false,true))
assert(picked[#picked]:find('fox0%.png'))
a.skin=2
assert(Art.drawHero(o,a,0,true,true))
assert(picked[#picked]:find('frog0%.png'))
assert(o.usesOriginalEnemy)
assert(not o.usesOriginalHero)
-- Keep player art independent from enemy assets.
assert(Art.drawHero(o,a,0,false,false))
assert(picked[#picked]:find('player%.png'))
assert(o.usesOriginalHero)
assert(not Art.drawHero(Art.prepare({}, {hero}, atlases),a,0,false,true))
print('ARENA ENEMY CATALOG LUA OK')
