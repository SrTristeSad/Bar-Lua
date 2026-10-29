package.path='./?.lua;./?/init.lua;'..package.path
local A=require('src.love_affine')
local values
local transform={
    setMatrix=function(self,...)
        assert(select('#',...)==16,'LÖVE requires a 4x4 matrix')
        values={...}
    end
}
assert(A.set(transform,{a=2,b=3,c=4,d=5,tx=6,ty=7})==transform)
local expected={2,4,0,6,3,5,0,7,0,0,1,0,0,0,0,1}
for i=1,16 do assert(values[i]==expected[i],i) end
local applied
love={math={newTransform=function() return transform end},
      graphics={applyTransform=function(t)applied=t end}}
A.apply({a=1,b=0,c=0,d=1,tx=23,ty=-17})
assert(applied==transform and values[4]==23 and values[8]==-17)
local ok=pcall(function()A.set(transform,{a=2})end)
assert(not ok)
print('LOVE AFFINE LUA OK')
