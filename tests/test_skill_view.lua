package.path = './?.lua;./?/init.lua;'..package.path
local v = require('src.skill_view')
assert(v.display(nil) == nil)
assert(v.display({id='x',skill_id=5}) == nil)
local t={id=10039,name='Ataque básico',kind=1,button=2,skill_id=4010020,skill_name='Ataque'}
local d = v.display(t)
assert(d.skill_id==4010020 and d.button==2)
local texts={}
local panel={x=0,y=0,w=800,h=600,small={},background=function()end,
             put=function(s) texts[#texts+1]=tostring(s) end}
v.draw(t,panel,{functionbindskill=566,heroskillconfig=31119,functiondamage=687})
assert(#texts>=9)
local found=false
for _,line in ipairs(texts) do if line:find('4010020',1,true) then found=true end end
assert(found)
v.draw(nil,panel,nil)
print('F21 skill_view OK')
