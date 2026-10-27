package.path = './?.lua;./?/init.lua;' .. package.path
local g = require('src.sprite_geometry')
local function eq(a,b,label) assert(math.abs(a-b)<1e-5,(label or '')..': '..a..' != '..b) end
local f={w=20,h=10,source_w=80,source_h=60,offset_x=-11,offset_y=7}
local a,b,c,d=g.bounds(f)
eq(a,-21,'left');eq(b,2,'bottom');eq(c,-1,'right');eq(d,12,'top')
local x,y,r,sx,sy=g.placement(f)
eq(x,-21);eq(y,12);eq(r,0);eq(sx,1);eq(sy,-1)
eq(select(1,g.center(f,0,0)),29)
local rframe={w=10,h=20,rotated=true,offset_x=3,offset_y=-2}
a,b,c,d=g.bounds(rframe)
eq(a,-7);eq(b,-7);eq(c,13);eq(d,3)
x,y,r,sx,sy=g.placement(rframe)
eq(x,-7);eq(y,-7);eq(r,math.pi/2);eq(sx,1);eq(sy,-1)
local call
love={graphics={draw=function(...) call={...} end}}
g.draw('img','quad',f)
assert(call and call[1]=='img' and call[2]=='quad' and call[7]==-1)
print('Testes sprite geometry: OK')
