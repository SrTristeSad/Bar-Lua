package.path = './?.lua;./?/init.lua;' .. package.path
local resolve = require('src.sprite_resolver')
local a = {path='character/effect/resource_effect20.bplist', frames={
  {name='hero.png', x=1}, {name='flame.png', x=2}}}
local b = {path='character/other/resource_other.bplist', frames={
  {name='hero.png', x=3}, {name='smoke.png', x=4}}}
local index = resolve.index({a, b})
assert(resolve.find(index,{path='character/effect/a.bexportjson',atlas_files={'resource_effect20.plist'}}, 'hero.png').atlas == a)
assert(resolve.find(index,{path='character/other/b.bexportjson',atlas_files={'resource_other.plist'}}, 'hero.png').atlas == b)
assert(resolve.find(index,{path='character/neutral/c.bexportjson'}, 'hero.png') == nil, 'ambíguo não deve ser escolhido')
assert(resolve.find(index,{path='character/neutral/c.bexportjson'}, 'smoke.png').atlas == b, 'único global')
assert(resolve.find(index,{path='character/effect/a.bexportjson'}, 'flame.png').atlas == a, 'local')
assert(resolve.find(index,{path='character/effect/a.bexportjson'}, 'inexistente.png') == nil)
print('Testes sprite resolver: OK')
