package.path='./?.lua;./?/init.lua;'..package.path
local C=require('src.contact_filter')
local V=require('src.filter_view')
local F=C.filterForCollidable
assert(C.shouldCollide(F(true),F(true)))
assert(not C.shouldCollide(F(true),F(false)))
assert(not C.shouldCollide(F(false),F(true)))
assert(not C.shouldCollide(F(false),F(false)))
local a,b=F(false),F(false)
a.groupIndex=5;b.groupIndex=5
assert(C.shouldCollide(a,b))
a.groupIndex=-5;b.groupIndex=-5
assert(not C.shouldCollide(a,b))
a={categoryBits=2,maskBits=4,groupIndex=0}
b={categoryBits=4,maskBits=2,groupIndex=0}
assert(C.shouldCollide(a,b))
b.maskBits=0
assert(not C.shouldCollide(a,b))
local ok=pcall(C.shouldCollide,{categoryBits=1.2,maskBits=2,groupIndex=0},F(true))
assert(not ok)
V.reset()
assert(select(3,V.state())==true)
assert(V.keypressed('a'))
assert(select(3,V.state())==false)
assert(V.keypressed('g'))
assert(select(3,V.state())==true)
assert(V.keypressed('g'))
assert(select(3,V.state())==false)
assert(V.keypressed('r'))
assert(select(3,V.state())==true)
local messages={}
local panel={x=0,y=0,w=1000,h=650,small={},background=function() end,put=function(s) messages[#messages+1]=tostring(s) end}
V.draw(nil,panel)
assert(table.concat(messages,' '):find('ShouldCollide',1,true))
print('F17 filter/view OK')
