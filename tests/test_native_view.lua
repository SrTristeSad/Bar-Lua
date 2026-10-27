package.path = './?.lua;./?/init.lua;' .. package.path
local view = require('src.native_view')
assert(#view.entries({name='Hero',methods={}})==0)
local list = view.entries({name='Hero',methods={{signature='Hero::setEnergy(int)',address='0x2010',bytes=64}}})
assert(#list==1)
assert(list[1]:find('0x2010',1,true))
assert(list[1]:find('Hero::setEnergy',1,true))
print('FASE11 NATIVE VIEW OK')
