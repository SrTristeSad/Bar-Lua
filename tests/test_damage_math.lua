package.path = './?.lua;./?/init.lua;'..package.path
local lib = require('src.damage_math')
local function near(a,b) assert(math.abs(a-b)<1e-6, tostring(a)..' ~= '..tostring(b)) end
local p = {A=100,B=25,C=20,D_percent=150,E=10,threshold=25.9}
local critical = assert(lib.core(p,25))
near(critical.base,80)
near(critical.partial,108)
assert(critical.triggered)
local normal = assert(lib.core(p,26))
near(normal.partial,72)
assert(not normal.triggered)
local zero = assert(lib.core({A=0,B=0,C=0,D_percent=100,E=0,threshold=0}, 1))
near(zero.partial,0)
assert(lib.core({},1)==nil)
assert(lib.core(p,0,0)==nil)
assert(lib.core(p,0/0)==nil)
assert(lib.core({A=1,B=2,C=3,D_percent=100,E=0,threshold=math.huge},3)==nil)
local view = require('src.damage_math_view')
assert(view.keypressed('right'))
assert(view.keypressed('up'))
assert(not view.keypressed('space'))
local outputs={}
view.draw({name='audit',ratio=100,instructions=332,checked=29},{
 x=0,y=0,w=800,h=650,small={},
 background=function() end,
 put=function(t)outputs[#outputs+1]=t end
})
assert(table.concat(outputs,' '):find('NÃO',1,true) or table.concat(outputs,' '):find('não',1,true))
print('F24 DAMAGE MATH LUA OK')
