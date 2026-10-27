package.path='./?.lua;./?/init.lua;'..package.path
local r=require('src.scene_resources')
local atlases={
 {path='gui/gui.bplist',image='gui/gui.png',frames={{name='Ver_6/Sliced/di.png',x=4,y=8,w=20,h=30}}},
 {path='gui/icon.bplist',image='gui/icon.png',frames={{name='foo.png',x=0,y=0,w=10,h=10}}},
}
local index=r.build(atlases,{['gui/loose.png']='gui/LoOsE.png'})
local asset=r.find(index,{path='Gui/gui/Ver_6/Sliced/di.png',type=0})
assert(asset.kind=='atlas' and asset.atlas==atlases[1] and asset.frame.x==4)
assert(r.find(index,{path='GUI/LOOSE.PNG',type=0}).path=='gui/LoOsE.png')
assert(r.find(index,{path='unknown.png',type=0})==nil)
assert(r.find(index,{path='Gui/gui/Ver_6/Sliced/di.png',type=1})==nil)
assert(r.find(index,{path='../gui/gui/Ver_6/Sliced/di.png',type=0})==nil)
-- Uma referencia repetida nunca pode escolher arbitrariamente um atlas.
local duplicate=r.build({atlases[1],atlases[1]}, {})
assert(r.find(duplicate,{path='gui/gui/Ver_6/Sliced/di.png',type=0})==nil)
print('Testes scene_resources: OK')
