package.path='./?.lua;./?/init.lua;'..package.path
local C=require('src.arena_collision')
local G=require('src.arena_game')
local function gap(a,b)
    local dx,dy=a.x-b.x,a.y-b.y
    return math.sqrt(dx*dx+dy*dy)-(a.radius+b.radius)
end
local g=G.new(1200,780)
-- Several overlapping actors must separate, including exact coincidence.
g.player.x,g.player.y=600,390
for _,e in ipairs(g.enemies) do
    e.x,e.y=600,390
    e.cooldown=999
end
C.solve(g,35)
for i,e in ipairs(g.enemies) do
    assert(gap(g.player,e)>-0.03,'player intersects enemy '..i)
    for j=i+1,#g.enemies do
        assert(gap(e,g.enemies[j])>-0.03,'enemies intersect')
    end
end
-- No actor should leave the arena when pushed near the left edge.
g.player.x,g.player.y=5,60
for _,e in ipairs(g.enemies) do e.x,e.y=5,60 end
C.solve(g,50)
assert(g.player.x>=g.player.radius+16)
assert(g.player.y>=g.player.radius+46)
for _,e in ipairs(g.enemies) do
    assert(e.x>=e.radius+12 and e.y>=e.radius+42)
    assert(gap(g.player,e)>-0.05)
end
-- Dead bodies do not affect movement or block combat actors.
g=G.new()
local a=g.enemies[1]
a.alive=false
a.x,a.y=g.player.x,g.player.y
local x,y=g.player.x,g.player.y
C.solve(g,12)
assert(g.player.x==x and g.player.y==y)
-- Steering alters pursuit direction when a teammate is nearby.
local p={x=500,y=400}
local e={x=200,y=400,radius=17,skin=1,alive=true}
local o={x=222,y=418,radius=17,skin=2,alive=true}
local vx,vy,dist=C.steer(e,p,{e,o})
assert(dist==300 and vx>0 and vy<0)
local soloX,soloY=C.steer(e,p,{e})
assert(math.abs(soloX-1)<1e-8 and math.abs(soloY)<1e-8)
-- Sustained AI movement must not stack enemies on the player.
g=G.new(1280,720)
for _,en in ipairs(g.enemies) do
    en.cooldown=9999
    en.speed=240
end
for _=1,180 do G.update(g,1/60,{}) end
for i,en in ipairs(g.enemies) do
    assert(gap(g.player,en)>-0.07,'AI overlaps player after chasing '..i)
    for j=i+1,#g.enemies do
        assert(gap(en,g.enemies[j])>-0.07,'AI actors overlap after chasing')
    end
end
-- Collision system does not change the combat state's win/loss conditions.
g=G.new()
g.player.hp=1
a=g.enemies[1]
a.x,a.y=g.player.x+30,g.player.y
a.cooldown=0
G.update(g,0.02,{})
assert(g.phase=='lost' and g.player.hp==0)
print('ARENA COLLISION AND AI LUA OK')
