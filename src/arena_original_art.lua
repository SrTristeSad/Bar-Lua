-- Original BarbarQ asset bridge for the playable arena.
-- Reuses recovered TMX maps, armature tracks and plist sprite metadata.
-- Timing, orientation mapping and all combat rules remain provisional.
local resolver = require('src.sprite_resolver')
local pose = require('src.pose')
local geometry = require('src.sprite_geometry')
local Art = {}
local function pickMap(maps)
    for _, map in ipairs(maps or {}) do
        if map.name=='petisland_01' then return map end
    end
    return (maps or {})[1]
end
local function pickHero(animations)
    for _, asset in ipairs(animations or {}) do
        if asset.path=='character/babarian/babarian.bexportjson' then return asset end
    end
end
local function movement(asset, action, variant)
    if not asset then return nil end
    local name=action..'_'..tostring(variant or 0)
    for _,arm in ipairs(asset.animations or {}) do
        for _,move in ipairs(arm.movements or {}) do
            if move.name==name and move.duration and move.duration>0 then return move end
        end
    end
end
Art.movement=movement
function Art.prepare(maps, animations, atlases)
    local map=pickMap(maps)
    local hero=pickHero(animations)
    local result={
        map=map, hero=hero,
        spriteIndex=resolver.index(atlases or {}),
        images={}, quads={}, tiles={},
        drawnTiles=0, drawnBones=0, missingTextures=0,
        usesOriginalMap=false, usesOriginalHero=false
    }
    return result
end
function Art.bounds(art)
    if not art or not art.map then return nil end
    local m=art.map
    if type(m.width)~='number' or type(m.height)~='number' or
       type(m.tilewidth)~='number' or type(m.tileheight)~='number' or
       m.width<1 or m.height<1 then return nil end
    return m.width*m.tilewidth, m.height*m.tileheight
end
function Art.camera(art, player)
    local ww,hh=Art.bounds(art)
    if not ww then return {scale=1,x=0,y=0} end
    local s=1.20
    local visW,visH=1280/s,720/s
    local cx=ww<=visW and ww/2 or math.max(visW/2,math.min(ww-visW/2,player.x))
    local cy=hh<=visH and hh/2 or math.max(visH/2,math.min(hh-visH/2,player.y))
    return {scale=s,x=640-cx*s,y=360-cy*s}
end
local function image(art, path)
    if not path then return nil end
    if art.images[path]~=nil then return art.images[path] or nil end
    local ok, img=pcall(love.graphics.newImage, 'assets_original/'..path)
    if not ok or not img then
        art.images[path]=false
        art.missingTextures=art.missingTextures+1
        return nil
    end
    img:setFilter('nearest','nearest')
    art.images[path]=img
    return img
end
local function quad(art, key, img, x,y,w,h)
    if art.quads[key]~=nil then return art.quads[key] or nil end
    if x<0 or y<0 or w<1 or h<1 or x+w>img:getWidth() or y+h>img:getHeight() then
        art.quads[key]=false
        return nil
    end
    local q=love.graphics.newQuad(x,y,w,h,img:getDimensions())
    art.quads[key]=q
    return q
end
local function layerTiles(art, layer, width, height)
    if art.tiles[layer] then return art.tiles[layer] end
    local cells,n={},0
    for _,run in ipairs(layer.runs or {}) do
        local value,count=run[1],run[2]
        if type(count)~='number' or count<0 or count>width*height then return nil end
        for _=1,count do
            n=n+1
            if n>width*height then return nil end
            cells[n]=value
        end
    end
    if n~=width*height then return nil end
    art.tiles[layer]=cells
    return cells
end
Art.layerTiles=layerTiles
function Art.drawMap(art, player)
    local m=art and art.map
    if not m then return 0 end
    local camera=Art.camera(art, player)
    local s=camera.scale
    local mincol=math.max(0,math.floor((-camera.x/s)/m.tilewidth))
    local maxcol=math.min(m.width-1,math.ceil(((1280-camera.x)/s)/m.tilewidth))
    local minrow=math.max(0,math.floor((-camera.y/s)/m.tileheight))
    local maxrow=math.min(m.height-1,math.ceil(((720-camera.y)/s)/m.tileheight))
    local count=0
    for _,layer in ipairs(m.layers or {}) do
        local cells=layerTiles(art,layer,m.width,m.height)
        if cells then
            for row=minrow,maxrow do
                for col=mincol,maxcol do
                    local gid=(cells[row*m.width+col+1] or 0)%536870912
                    if gid>0 then
                        local ts
                        for i=#m.tilesets,1,-1 do
                            if gid>=m.tilesets[i].firstgid then ts=m.tilesets[i];break end
                        end
                        if ts then
                            local img=image(art,ts.image)
                            if img then
                                local id=gid-ts.firstgid
                                local cols=ts.columns
                                if not cols or cols<=0 then
                                    cols=math.floor((img:getWidth()-ts.margin*2+ts.spacing)/
                                        (ts.tilewidth+ts.spacing))
                                end
                                if cols>0 and id>=0 then
                                    local x=ts.margin+(id%cols)*(ts.tilewidth+ts.spacing)
                                    local y=ts.margin+math.floor(id/cols)*(ts.tileheight+ts.spacing)
                                    local q=quad(art,ts.image..':'..id,img,x,y,ts.tilewidth,ts.tileheight)
                                    if q then
                                        love.graphics.setColor(1,1,1,1)
                                        love.graphics.draw(img,q,col*m.tilewidth,row*m.tileheight,0,
                                            m.tilewidth/ts.tilewidth,m.tileheight/ts.tileheight)
                                        count=count+1
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    art.drawnTiles=count
    art.usesOriginalMap=count>0
    return count
end
local function chooseDirection(p)
    -- Recovered moves have 5 direction variants, but native direction-to-variant mapping
    -- still needs verification; use deterministic approximation only for alpha.
    local dx,dy=p.faceX or 1,p.faceY or 0
    if dx>=0 then
        if dy< -0.35 then return 1 end
        if dy>0.35 then return 2 end
        return 0
    end
    if dy< -0.35 then return 3 end
    return 4
end
function Art.drawHero(art,p,elapsed,attacking,enemy)
    if not art or not art.hero then return false end
    local arm=art.hero.armatures and art.hero.armatures[1]
    if not arm then return false end
    local variant=chooseDirection(p)
    local action=attacking and 'attack1' or ((p.walking or enemy) and 'walk' or 'stand')
    local mov=movement(art.hero,action,variant)
    if not mov then mov=movement(art.hero,action,0) end
    if not mov then mov=movement(art.hero,'stand',0) end
    if not mov then return false end
    local frame
    if attacking then
        -- Compressed to the alpha cooldown (not the game's original fps).
        local progress=1-math.min(1,p.cooldown/math.max(p.attackCooldown,0.001))
        frame=progress*math.max(0,mov.duration-0.001)
    else
        frame=(elapsed*30)%mov.duration -- provisional playback rate
    end
    local nodes=pose.ordered(pose.evaluate(arm,mov,frame,true,true))
    local drawn=0
    love.graphics.push()
    love.graphics.translate(p.x,p.y)
    for _,node in ipairs(nodes) do
        local index=node.display_index
        local display=index and index>=0 and node.bone.displays and node.bone.displays[index+1]
        local sprite=display and resolver.find(art.spriteIndex,art.hero,display)
        if sprite and node.matrix then
            local img=image(art,sprite.atlas.image)
            if img then
                local f=sprite.frame
                local q=quad(art,sprite.atlas.path..':'..f.name,img,f.x,f.y,f.w,f.h)
                if q then
                    love.graphics.push()
                    love.graphics.scale(1,-1)
                    local mat=node.matrix
                    local transform=love.math.newTransform()
                    transform:setMatrix(mat.a,mat.b,mat.c,mat.d,mat.tx,mat.ty)
                    love.graphics.applyTransform(transform)
                    love.graphics.setColor(1,1,1,1)
                    geometry.draw(img,q,f)
                    love.graphics.pop()
                    drawn=drawn+1
                end
            end
        end
    end
    love.graphics.pop()
    art.drawnBones=drawn
    if drawn>0 then art.usesOriginalHero=true end
    return drawn>0
end
return Art
