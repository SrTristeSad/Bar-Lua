package.path='./?.lua;./?/init.lua;'..package.path
local P=require('src.playtest')
local x,y,moving=P.inputVector(false,false,false,false)
assert(x==0 and y==0 and not moving)
x,y,moving=P.inputVector(true,false,false,true)
assert(moving and math.abs(x*x+y*y-1)<1e-12 and y<0 and x>0)
assert(P.findHero({{path='a'},{path='character/babarian/babarian.bexportjson', animations={}}}).path:find('babarian'))
local a = {animations={{movements={{name='stand_0',duration=41},{name='walk_0',duration=60},{name='walk_4',duration=30},{name='walk_1',duration=0}}}}}
assert(P.movement(a,false,0).name=='stand_0')
assert(P.movement(a,true,0).duration==60)
assert(P.movement(a,true,1)==nil)
assert(P.movement(a,true,4).duration==30)
assert(not P.setVariant(-1) and not P.setVariant(5))
-- Fake físico estrito: testa a integração de chamadas, não substitui uma simulação real.
local bodies, fixtures, steps = {},{},0
local World={}
function World:update(dt)
    assert(math.abs(dt-1/60)<1e-9)
    steps=steps+1
    for _,b in ipairs(bodies) do
        if b.kind=='dynamic' then b.x=b.x+(b.vx or 0)*dt;b.y=b.y+(b.vy or 0)*dt end
    end
end
function World:setCallbacks(cb) self.callback=cb end
local function body(world,x,y,kind)
    local b={x=x,y=y,kind=kind}
    function b:setFixedRotation(bol) assert(bol) end
    function b:getPosition() return self.x,self.y end
    function b:setLinearVelocity(vx,vy) self.vx,self.vy=vx,vy end
    bodies[#bodies+1]=b
    return b
end
local fixture=function(b,shape,density)
    assert(b and shape and density==1)
    local f={body=b}
    function f:setFilterData(category,mask,group)
        assert(category==1 and mask==3 and group==0)
        self.filter={category,mask,group}
    end
    function f:setFriction() end
    function f:setRestitution() end
    fixtures[#fixtures+1]=f
    return f
end
love={physics={
    setMeter=function(n) assert(n==30) end,
    newWorld=function(x,y,sleep) assert(x==0 and y==0 and sleep);return setmetatable({}, {__index=World}) end,
    newBody=body,newCircleShape=function(r) assert(r==18);return {r=r} end,
    newRectangleShape=function(w,h) return {w=w,h=h} end,
    newFixture=fixture,
}}
local map={name='petisland_01',width=16,height=10,tilewidth=64,tileheight=64}
assert(not P.start({},a,{}))
assert(not P.state().ready)
assert(P.start(map,a,{}))
assert(P.state().ready and #fixtures==6) -- player, 4 limites, 1 obstáculo de TESTE
assert(#bodies==6 and P.state().obstacle)
local initialX,initialY=P.playerPosition()
assert(initialX==512 and initialY==320)
local n=0
P.update(1/60,function(k) return k=='d' end)
local nextX,nextY=P.playerPosition()
assert(nextX>initialX and nextY==initialY and steps==1)
P.update(1/60,function() return false end)
assert(P.state().body.vx==0 and P.state().body.vy==0)
assert(P.setVariant(4) and P.state().directions==4)
local collisionDebug=P.state().collisionDebug
P.toggleDebug()
assert(P.state().collisionDebug~=collisionDebug)
P.reset()
assert(not P.state().ready and P.playerPosition()==nil)
-- Sprite fallback explícito quando recursos não estão prontos
assert(not P.start(map,nil,{}))
print('F18 playtest unitário OK')