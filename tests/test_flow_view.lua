package.path = './?.lua;./?/init.lua;'..package.path
local view = require('src.flow_view')
local data = {name='Hero::setStickDir(int)', address='0xe5983c', bytes=8,
    instructions=2, direct=0, indirect=0, branches=0, comparisons=0,
    calls={{name='um alvo', count=2, address='0x1', external=true}}}
local rows = view.rows(data)
assert(#rows == 1 and rows[1].count == 2 and rows[1].external == true)
assert(#view.rows({}) == 0)
assert(#view.rows(nil) == 0)
local prints, scissor = {}, 0
love = {graphics={setScissor=function(...) scissor=scissor+1 end}}
local panel = {x=0,y=0,w=800,h=480,small={},
   background=function(...) end,
   put=function(label,...) prints[#prints+1]=label end}
view.draw(data, panel)
assert(scissor == 2)
assert(table.concat(prints,' '):find('setStickDir',1,true))
assert(table.concat(prints,' '):find('um alvo',1,true))
print('flow_view tests OK')