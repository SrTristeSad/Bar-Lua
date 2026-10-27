package.path='./?.lua;./?/init.lua;'..package.path
local view=require('src.movement_view')
view.reset()
local start=view.values()
assert(start.speed==100 and start.encoded==23)
assert(view.keypressed('right'))
assert(view.values().encoded==24)
assert(view.keypressed('up'))
assert(view.values().speed==110)
assert(view.keypressed('k'))
assert(view.keypressed('a'))
assert(view.keypressed('q'))
assert(not view.keypressed('f1'))
local linecount,printcount=0,0
love={graphics={setColor=function() end, line=function() linecount=linecount+1 end,
    circle=function() end}}
view.draw(nil,{x=0,y=0,w=880,h=600,small={},background=function() end,
    put=function(s) printcount=printcount+1 end})
assert(linecount==5 and printcount>=9)
view.reset()
assert(view.values().speed==100)
print('movement view tests OK')