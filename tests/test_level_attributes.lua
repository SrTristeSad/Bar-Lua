package.path='./?.lua;./?/init.lua;'..package.path
local model=require('src.level_attributes')
local catalog=dofile('cache/hero_levels.lua')
local found
for _,g in ipairs(catalog.groups) do if g.base_id==210001 then found=g;break end end
assert(found and #found.levels>=3)
assert(model.value(found,1,'0x38')==195)
assert(model.value(found,2,'0x38')==200)
assert(model.value(found,3,'0x38')==205)
assert(model.value(found,1,'0x54')==8)
local delta=assert(model.diff(found,1,3))
assert(delta['0x38']==10)
assert(delta['0x3c']==0)
assert(model.value(found,999,'0x38')==nil)
assert(model.value(found,1,'HP')==nil)
assert(model.diff(found,0,1)==nil)
assert(model.diff({levels={}},1,2)==nil)
print('F29 LEVEL ATTRIBUTES LUA OK')
