package.path='./?.lua;./?/init.lua;' ..package.path
love={graphics={setColor=function() end,line=function()end,circle=function()end}}
local view=require('src.entity_move_view')
local panel={x=0,y=0,w=960,h=620,small={},background=function()end,put=function()end}
view.reset()
assert(view.values().kind=='set_transform')
view.draw(nil,panel)
assert(view.keypressed('g') and view.values().kind=='write_velocity')
assert(view.keypressed('t') and view.values().kind=='none')
assert(view.keypressed('r') and view.values().kind=='set_transform')
assert(view.keypressed('z') and view.values().kind=='none')
assert(view.keypressed('right'))
assert(view.keypressed('return'))
assert(view.x>0)
assert(not view.keypressed('invalid'))
print('entity view tests OK')
