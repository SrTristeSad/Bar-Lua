package.path = './?.lua;./?/init.lua;'..package.path
local trace = dofile('cache/skill_trace.lua')
local view = require('src.skill_view')
local row = {id=10039,name='ataque',kind=1,button=2,skill_id=4010020,skill_name='ataque'}
local example = assert(view.trace(trace,4010020))
assert(example.incoming_total == 1 and example.outgoing_total == 0)
assert(example.incoming[1].id == 10039)
local calls = {}
local panel = {x=0,y=0,w=700,h=720,small=1,
    background=function(...) end,
    put=function(s) calls[#calls+1]=tostring(s) end}
view.draw(row,panel,{functionbindskill=566,heroskillconfig=31119,functiondamage=687},trace)
assert(#calls > 10)
assert(assert(loadfile('main.lua')))
print('F22 OK')
