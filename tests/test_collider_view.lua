package.path='./?.lua;./?/init.lua;'..package.path
local module=require('src.collider_view')
local catalog=require('reports.native_colliders')
assert(#catalog==2)
local printed={}
local panel={x=0,y=0,w=1000,h=620,small={},background=function() end,
  put=function(s) printed[#printed+1]=tostring(s) end}
for _,item in ipairs(catalog) do
  assert(module.describe(item) and #module.describe(item)>=4)
  module.draw(item,panel)
end
assert(table.concat(printed,' '):find('100',1,true))
assert(table.concat(printed,' '):find('polígono',1,true))
module.draw(nil,panel)
assert(table.concat(printed,' '):find('ausente',1,true))
print('collider view OK')
