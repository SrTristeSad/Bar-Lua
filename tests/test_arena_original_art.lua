package.path='./?.lua;./?/init.lua;'..package.path
local Art=require('src.arena_original_art')
local G=require('src.arena_game')
local map={name='petisland_01',width=2,height=2,tilewidth=32,tileheight=32,
    tilesets={{firstgid=1,image='test_tiles.png',columns=2,spacing=0,margin=0,
               tilewidth=32,tileheight=32}},
    layers={{runs={{1,2},{2,2}}}}}
local hero={path='character/babarian/babarian.bexportjson',
    atlas_files={'babarian.plist'},
    armatures={{bones={{name='root',initial_display=0,displays={'sprite0'}}}}},
    animations={{movements={{name='stand_0',duration=30,tracks={}},
                            {name='walk_0',duration=30,tracks={}},
                            {name='attack1_0',duration=61,tracks={}}}}}}
local atlases={{path='character/babarian/babarian.bplist',
    image='test_hero.png',
    frames={{name='sprite0',x=0,y=0,w=20,h=20,source_w=20,source_h=20}}}}
local o=Art.prepare({map},{hero},atlases)
assert(o.map==map and o.hero==hero)
assert(Art.movement(hero,'walk',0).name=='walk_0')
assert(Art.bounds(o)==64)
local w,h=Art.bounds(o);assert(w==64 and h==64)
local camera=Art.camera(o,{x=32,y=32})
assert(camera.scale>0 and type(camera.x)=='number')
local tiles=Art.layerTiles(o,map.layers[1],2,2)
assert(#tiles==4 and tiles[1]==1 and tiles[4]==2)
assert(Art.layerTiles(o,{runs={{1,5}}},2,2)==nil)
local counter={tiles=0,hero=0}
local function image(path)
    assert(path:find('assets_original/',1,true)==1)
    return {getWidth=function()return 64 end,
            getHeight=function()return 64 end,
            getDimensions=function()return 64,64 end,
            setFilter=function()end}
end
love={
    graphics={
        newImage=image,
        newQuad=function()return {quad=true} end,
        setColor=function()end,
        draw=function(_,quad)
            if quad then counter.tiles=counter.tiles+1
            else counter.hero=counter.hero+1 end
        end,
        push=function()end,pop=function()end,
        translate=function()end,scale=function()end,
        applyTransform=function()end,
    },
    math={newTransform=function()
        return {setMatrix=function()end}
    end},
}
assert(Art.drawMap(o,{x=32,y=32})==4)
assert(o.usesOriginalMap and o.drawnTiles==4)
assert(Art.drawHero(o,{x=32,y=32,faceX=1,faceY=0,walking=false,
    attackCooldown=0.42,cooldown=0},0,false,false))
assert(o.usesOriginalHero and o.drawnBones==1)
assert(counter.tiles>=5)
assert(Art.drawHero(o,{x=32,y=32,faceX=1,faceY=0,walking=true,
    attackCooldown=0.42,cooldown=0.21},0,true,false))
-- Without metadata or files, fall back to the procedural arena, without failure.
local fallback=Art.prepare({}, {}, {})
assert(Art.bounds(fallback)==nil)
assert(not Art.drawHero(fallback,{x=0,y=0},0,false,false))
assert(Art.drawMap(fallback,{x=0,y=0})==0)
local g=G.new(1024,640)
assert(g.width==1024 and g.height==640)
assert(g.player.x==512 and g.player.y==320)
print('ORIGINAL ARENA ART LUA OK')
