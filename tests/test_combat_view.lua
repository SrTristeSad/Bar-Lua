package.path = './?.lua;./?/init.lua;'..package.path
local view = require('src.combat_view')
assert(view.details(nil) == nil)
assert(view.details({name='CDamageFunction::Run(target)', address='0xe53070', instructions=70}).instructions == 70)
local text = {}
local panel = {x=0,y=0,w=900,h=640,background=function()end,small=false,
    put=function(t) text[#text+1] = tostring(t) end}
view.draw({name='CDamageFunction::Run(target)',address='0xe53070',instructions=70,
    checks={'get_damage_value','hero_hurt'}},panel)
local merged = table.concat(text, '\n')
assert(merged:find('get_damage_value',1,true))
assert(merged:find('NÃO reproduzidos',1,true))
text = {}
view.draw(nil,panel)
assert(table.concat(text):find('Sem relatório',1,true))
print('test_combat_view: OK')
