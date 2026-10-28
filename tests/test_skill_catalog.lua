package.path = './?.lua;./?/init.lua;'..package.path
local data=dofile('cache/skill_catalog.lua')
assert(#data.links==566)
assert(data.tables.heroskillconfig==31119)
local found=false
for _,link in ipairs(data.links) do
  assert(type(link.id)=='number' and type(link.name)=='string')
  assert(type(link.button)=='number' and type(link.skill_id)=='number')
  if link.id==10039 then
    assert(link.skill_id==4010020 and link.button==2)
    found=true
  end
end
assert(found)
local chunk=assert(loadfile('main.lua'))
print('F21 skill_catalog OK')
