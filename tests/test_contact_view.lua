package.path='./?.lua;./?/init.lua;'..package.path
local view=require('src.contact_view')
local data=require('reports.native_contacts')
assert(#data==8)
local seen={}
for _,item in ipairs(data) do
  assert(not seen[item.name])
  seen[item.name]=true
  assert(item.instructions>0 and view.describe(item))
end
local out={}
local panel={x=0,y=0,w=900,h=580,small={},background=function() end,
 put=function(text) out[#out+1]=text end}
view.draw(data[1],panel)
assert(table.concat(out,' '):find('SOMENTE leitura',1,true))
view.draw(nil,panel)
assert(table.concat(out,' '):find('indisponível',1,true))
print('contact view tests OK')
