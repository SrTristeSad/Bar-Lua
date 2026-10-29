package.path='./?.lua;./?/init.lua;'..package.path
local G=require('src.arena_game')
local function near(a,b) return math.abs(a-b)<0.0001 end
local s=G.new()
assert(s.phase=='playing' and s.wave==1 and G.aliveEnemies(s)==3)
assert(s.player.hp==s.player.maxHp and s.player.damage==59)
local px,py=s.player.x,s.player.y
G.update(s,1/60,{right=true,down=true})
assert(s.player.x>px and s.player.y>py)
assert(near((s.player.x-px)^2+(s.player.y-py)^2,(s.player.speed/60)^2))
s=G.new()
-- Place a single target in front, others far away.
local e=s.enemies[1]
e.x=s.player.x+53; e.y=s.player.y; e.hp=100;e.maxHp=100
for i=2,#s.enemies do s.enemies[i].x=50;s.enemies[i].y=50 end
local ok,hits=G.attack(s)
assert(ok and hits==1 and e.hp==41)
assert(not G.attack(s))
for _=1,10 do G.update(s,0.05,{}) end
ok,hits=G.attack(s)
assert(ok and hits==1 and not e.alive and s.kills==1 and s.score==100)
assert(G.aliveEnemies(s)==2)
-- Facing to the left must not hit a target on the right.
s=G.new()
for i=2,#s.enemies do s.enemies[i].x=50;s.enemies[i].y=50 end
e=s.enemies[1];e.x=s.player.x+45;e.y=s.player.y
local initial=e.hp
s.player.faceX=-1;s.player.faceY=0
ok,hits=G.attack(s)
assert(ok and hits==0 and e.hp==initial)
-- Wave completion and transition.
s=G.new()
e=s.enemies[1];e.x=s.player.x+45;e.y=s.player.y;e.hp=59
for i=2,#s.enemies do s.enemies[i].alive=false end
ok,hits=G.attack(s)
assert(ok and hits==1 and s.phase=='between')
for _=1,35 do G.update(s,0.05,{}) end
assert(s.phase=='playing' and s.wave==2 and G.aliveEnemies(s)==4)
-- End of final wave produces a victory.
s=G.new();s.wave=3
e=s.enemies[1];e.x=s.player.x+45;e.y=s.player.y;e.hp=20
for i=2,#s.enemies do s.enemies[i].alive=false end
assert(G.attack(s) and s.phase=='won')
local oldScore=s.score
G.update(s,0.05,{right=true})
assert(s.score==oldScore and not G.attack(s))
-- Enemy contact can kill the player.
s=G.new()
e=s.enemies[1];e.x=s.player.x+10;e.y=s.player.y;e.cooldown=0
s.player.hp=5
G.update(s,0.05,{})
assert(s.phase=='lost' and s.player.hp==0)
-- Pause freezes movement and cooldown; resume restores it.
s=G.new();G.attack(s)
local before=s.player.cooldown
px=s.player.x
G.togglePause(s)
assert(s.phase=='paused')
G.update(s,1,{right=true})
assert(s.player.x==px and s.player.cooldown==before)
G.togglePause(s)
assert(s.phase=='playing')
G.update(s,0.05,{right=true})
assert(s.player.x>px and s.player.cooldown<before)
assert(G.new().player.hp==300)
print('ARENA GAMEPLAY LUA OK')
