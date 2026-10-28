package.path='./?.lua;./?/init.lua;'..package.path
local P=require('src.playtest')
local bodies,fixtures={},{}
local World={}
function World:update(dt) end
function World:setCallbacks(fn) self.callback=fn end
local function body(world,x,y,kind)
    local b={x=x,y=y,kind=kind}
    function b:getPosition() return self.x,self.y end
    function b:setFixedRotation(bool) end
    function b:setLinearVelocity(x,y) self.vx=x; self.vy=y end
    bodies[#bodies+1]=b
    return b
end
local function fixture(b,shape,density)
    local f={body=b}
    function f:setFilterData(c,m,g) self.filter={c,m,g} end
    function f:setFriction(n) end
    function f:setRestitution(n) end
    function f:setSensor(flag) self.sensor=flag end
    fixtures[#fixtures+1]=f
    return f
end
love={physics={setMeter=function()end,
    newWorld=function() return setmetatable({}, {__index=World}) end,
    newBody=body,newFixture=fixture,
    newCircleShape=function(r) return {r=r} end,
    newRectangleShape=function(w,h) return {w=w,h=h} end}}
local map={name='petisland_01',width=16,height=10,tilewidth=64,tileheight=64,
 objectgroups={{name='objects',objects={{id=3,shape='rectangle',x=395,y=138,width=232,height=238,rotation=0}}}}}
local hero={animations={}}
assert(P.start(map,hero,{}))
assert(#P.state().mapObjectRects==1)
assert(#P.state().mapObjectFixtures==1)
assert(P.state().mapObjectFixtures[1].sensor==true)
assert(not P.state().mapCollision)
assert(not P.toggleMapCollision()) -- personagem inicialmente dentro da area
assert(P.state().mapObjectFixtures[1].sensor==true)
P.state().body.x=180;P.state().body.y=250
assert(P.toggleMapCollision())
assert(P.state().mapCollision and P.state().mapObjectFixtures[1].sensor==false)
assert(P.toggleMapCollision())
assert(not P.state().mapCollision and P.state().mapObjectFixtures[1].sensor==true)
assert(P.toggleMapObjects()==false)
P.reset()
assert(#P.state().mapObjectFixtures==0)
print('F19 playtest TMX OK')
