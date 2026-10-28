package.path='./?.lua;./?/init.lua;'..package.path
local A=require('src.attack_preview')
local hero={animations={{movements={}}}}
for i=1,3 do for direction=0,4 do
    hero.animations[1].movements[#hero.animations[1].movements+1]={name=('attack%d_%d'):format(i,direction),duration=40+i}
end end
local s=A.new(hero,20)
assert(not A.begin(s,0,0) and not A.begin(s,4,0) and not A.begin(s,1,5))
assert(A.begin(s,2,3) and not A.begin(s,1,0))
local motion,frame=A.sample(s)
assert(motion.name=='attack2_3' and frame==0)
assert(not A.update(s,0.5))
motion,frame=A.sample(s)
assert(frame==10 and A.update(s,1.6) and A.sample(s)==nil)
assert(A.begin(s,1,4))
A.cancel(s)
assert(s.action==nil and A.sample(s)==nil)
print('F20 attack_preview OK')
