#!/usr/bin/env python3
"""Generate tiny ORIGINAL-FORMAT synthetic assets for an isolated LÖVE smoke test.

No proprietary images, maps or animation files are included.
"""
from __future__ import annotations
import shutil
import struct
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path("/tmp/bar-lua-visual-smoke")

def png(path, rgb):
    path.parent.mkdir(parents=True,exist_ok=True)
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    width=height=32
    raw=b"".join(b"\x00"+bytes((*rgb,255))*width for _ in range(height))
    data=(b"\x89PNG\r\n\x1a\n"+
          chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,6,0,0,0))+
          chunk(b"IDAT",zlib.compress(raw))+
          chunk(b"IEND",b""))
    path.write_bytes(data)

def asset(path,display):
    return """{path='%s',atlas_files={'sprites.plist'},
armatures={{bones={{name='root',initial_display=0,
displays={'%s'}}}}},animations={{movements={
{name='stand_0',duration=30,tracks={}},
{name='walk_0',duration=30,tracks={}},
{name='attack1_0',duration=30,tracks={}}
}}}}""" % (path,display)

def atlas(path,image,display):
    return """{path='%s',image='%s',
frames={{name='%s',x=0,y=0,w=16,h=16,source_w=16,source_h=16}}}""" % (path,image,display)

def main():
    if STAGE.exists():shutil.rmtree(STAGE)
    shutil.copytree(ROOT/"src",STAGE/"src")
    (STAGE/"cache").mkdir(parents=True)
    png(STAGE/"assets_original/map/tiles.png",(40,97,67))
    png(STAGE/"assets_original/character/babarian/sprites.png",(230,183,75))
    png(STAGE/"assets_original/character/smoke_enemy/sprites.png",(190,66,92))
    (STAGE/"cache/maps.lua").write_text("""
return {{name='petisland_01',width=20,height=14,tilewidth=64,tileheight=64,
tilesets={{firstgid=1,image='map/tiles.png',columns=2,spacing=0,margin=0,
tilewidth=32,tileheight=32}},
layers={{runs={{1,280}}}}}}
""",encoding="utf8")
    (STAGE/"cache/animations.lua").write_text("return {"+
        asset("character/babarian/babarian.bexportjson","player0")+","+
        asset("character/smoke_enemy/enemy.bexportjson","enemy0")+"}\n",encoding="utf8")
    (STAGE/"cache/atlases.lua").write_text("return {"+
        atlas("character/babarian/sprites.bplist","character/babarian/sprites.png","player0")+","+
        atlas("character/smoke_enemy/sprites.bplist","character/smoke_enemy/sprites.png","enemy0")+"}\n",encoding="utf8")
    (STAGE/"main.lua").write_text("""
io.stdout:setvbuf('no')
print('ARENA FIXTURE START')
local Art=require('src.arena_original_art')
local Game=require('src.arena_game')
local View=require('src.arena_view')
local art,game
local elapsed=0
function love.load()
    print('ARENA FIXTURE LOAD')
    art=Art.prepare(dofile('cache/maps.lua'),dofile('cache/animations.lua'),
                    dofile('cache/atlases.lua'))
    assert(#art.enemyAssets==1,'candidate enemy asset was not detected')
    game=Game.new(Art.bounds(art))
    game.player.cooldown=0.25
    game.enemies[1].attackVisual=0.12
    print('ARENA FIXTURE LOADED')
end
function love.update(dt)
    elapsed=elapsed+dt
    if elapsed>4 then
        print('ARENA VISUAL DID NOT DRAW')
        os.exit(3)
    end
end
function love.draw()
    print('ARENA FIXTURE DRAW')
    View.draw(game,1280,720,art)
    assert(art.usesOriginalMap,'TMX failed to render')
    assert(art.usesOriginalHero,'barbarian animation failed to render')
    assert(art.usesOriginalEnemy,'enemy animation failed to render')
    print('ARENA VISUAL SMOKE OK')
    love.event.quit(0)
end
""",encoding="utf8")
    print(str(STAGE))

if __name__=="__main__":
    main()
