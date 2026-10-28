package.path='./?.lua;./?/init.lua;'..package.path
local P=require('src.playtest')
local A=require('src.attack_preview')
local hero=P.findHero(dofile('cache/animations.lua'))
assert(hero)
for attack=1,3 do for dir=0,4 do
    local s=A.new(hero,30)
    assert(A.begin(s,attack,dir))
    local motion=A.sample(s)
    assert(motion.name==('attack%d_%d'):format(attack,dir))
    assert(motion.duration>=60)
end end
print('F20 15 animações reais OK')
