package.path='./?.lua;./?/init.lua;'..package.path
local view=require('src.level_attributes_view')
local db=dofile('cache/hero_levels.lua')
local group
for _,g in ipairs(db.groups) do if g.base_id==210001 then group=g;break end end
assert(group)
local drawn={}
local box={x=0,y=0,w=920,h=630,small='font',
    background=function()end,
    put=function(text)drawn[#drawn+1]=tostring(text)end}
view.draw(group,{total_instructions=696,total_checks=34},box)
local joined=table.concat(drawn,'\n')
assert(joined:find('210001',1,true))
assert(joined:find('195',1,true))
assert(view.keypressed('right'))
drawn={}
view.draw(group,{total_instructions=696,total_checks=34},box)
joined=table.concat(drawn,'\n')
assert(joined:find('220001',1,true))
assert(joined:find('200',1,true))
assert(view.keypressed('r'))
assert(not view.keypressed('invalid'))
print('F29 LEVEL UI LUA OK')
