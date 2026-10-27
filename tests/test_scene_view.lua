package.path = './?.lua;./?/init.lua;' .. package.path
local sceneView = require('src.scene_view')
local prints,rects,drawn = 0,0,0
local g={}
function g.setColor(...) end
function g.rectangle(...) rects=rects+1 end
function g.setScissor(...) end
function g.draw(...) drawn=drawn+1 end
function g.circle(...) end
love={graphics=g}
local object = {getDimensions=function() return 100,50 end}
local scene={path='setting.csb',name='Setting',root={class='Node', props={name='Setting',size={960,540},position={0,0},scale={1,1},anchor={0.5,0.5},visible=true},children={
 {class='ImageView', props={name='_Back',position={480,270},scale={1,1},anchor={0.5,0.5},size={960,540},visible=true,opacity=255},resource={path='Gui/back.png',type=0},children={}},
 {class='Button',props={name='Btn',position={80,400},size={45,30},visible=false},children={}}
}}}
local ctx={x=320,y=100,w=800,h=500,
  put=function(...) prints=prints+1 end,
  background=function(...) end,
  resolveImage=function(path,kind) assert(path=='Gui/back.png');return object end,
  small={}}
sceneView.draw(scene,ctx)
assert(rects>0 and prints>0 and drawn==1)
local entry,num=sceneView.inspect(scene)
assert(num==3 and entry.node.class=='Node')
sceneView.next(scene,1)
assert(sceneView.inspect(scene).node.class=='ImageView')
sceneView.next(scene,1)
assert(sceneView.inspect(scene).node.class=='Button')
sceneView.toggleGuides()
sceneView.toggleHidden()
sceneView.draw(scene,ctx)
sceneView.reset()
assert(sceneView.inspect(scene).node.class=='Node')
print('Testes scene_view: OK')