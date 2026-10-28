package.path='./?.lua;./?/init.lua;'..package.path
local M=require('src.reinit_rules')
assert(M.configId(201,1)==201)
assert(M.configId(201,4)==30201)
assert(M.configId(201,0)==nil)
assert(M.configId(201,2147483647)==nil)
local old={['0x38']=10,['0x3c']=20,['0x40']=30,['0x44']=40,['0x48']=50,['0x4c']=60,['0x50']=70}
local new={['0x38']=13,['0x3c']=18,['0x40']=35,['0x44']=41,['0x48']=44,['0x4c']=69,['0x50']=80}
local original={['0xc0']=100,['0x32c']=200,['0x330']=300,['0x310']=400,['0x314']=500,['0x328']=600,['0x318']=700,['0x31c']=800,['0x1b8']=900,other='keep'}
local flags={extra_204_active=false,nested_88_active=false}
local out,err=M.applySimpleDelta(old,new,original,flags)
assert(out,err)
local expected={['0xc0']=103,['0x32c']=198,['0x330']=305,['0x310']=401,['0x314']=501,['0x328']=594,['0x318']=709,['0x31c']=809,['0x1b8']=910,['0xe0']=44}
for k,v in pairs(expected) do assert(out[k]==v,k..' got '..tostring(out[k])) end
assert(out.other=='keep' and original['0xc0']==100 and original['0xe0']==nil)
assert(M.applySimpleDelta(old,new,original,{})==nil)
assert(M.applySimpleDelta(old,new,original,{extra_204_active=true,nested_88_active=false})==nil)
assert(M.applySimpleDelta(old,new,original,{extra_204_active=false,nested_88_active=true})==nil)
local broken={};for k,v in pairs(original) do broken[k]=v end;broken['0x314']=nil
assert(M.applySimpleDelta(old,new,broken,flags)==nil)
broken['0x314']=2147483647
assert(M.applySimpleDelta(old,new,broken,flags)==nil) -- overflow recusado
local ids=assert(M.newSkillIds({11,33},{33,7,11,7,8}))
assert(#ids==3 and ids[1]==7 and ids[2]==7 and ids[3]==8)
assert(M.newSkillIds({1},{'bad'})==nil)
local V=require('src.reinit_view')
assert(V.keypressed('up') and V.keypressed('down') and V.keypressed('right') and V.keypressed('left'))
assert(V.keypressed('r') and V.level==3 and V.delta==10)
assert(not V.keypressed('z'))
print('F28 REINIT LUA OK')
