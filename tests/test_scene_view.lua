package.path='./?.lua;./?/init.lua;'..package.path
local sceneView = require('src.scene_view')
local prints,rects,drawn,atlasDraws=0,0,0,0
local g={}
function g.setColor(...) end
function g.rectangle(...) rects=rects+1 end
function g.setScissor(...) end
function g.draw(image, quad, ...) drawn=drawn+1; if type(quad)=='table' then atlasDraws=atlasDraws+1 end end
function g.circle(...) end
function g.push(...) end
function g.pop(...) end
function g.translate(...) end
function g.scale(...) end
function g.shear(...) end
function g.rotate(...) end
function g.print(...) end
love={graphics=g}
local object={getDimensions=function() return 100,50 end}
local atlasQuad={}
local scene={path='setting.csb',name='Setting',root={class='Node', props={name='Setting',size={960,540},position={0,0},scale={1,1},anchor={0,0},visible=true},children={
 {class='ImageView', props={name='_Back',position={480,270},scale={1,1},anchor={0.5,0.5},size={960,540},visible=true,opacity=255},resource={path='Gui/back.png',type=0},children={}},
 {class='ImageView',props={name='AtlasImage',position={100,100},size={60,40},anchor={0.5,0.5},visible=true,z=1},resource={path='Gui/icon/hero.png',type=0},children={}},
 {class='Button',props={name='Btn',position={80,400},size={45,30},visible=false,z=2},children={}}
}}}
local ctx={x=320,y=100,w=800,h=500,
 put=function(...) prints=prints+1 end, background=function(...) end,
 resolveResource=function(r)
    if r.path=='Gui/back.png' then return {kind='image',image=object} end
    if r.path=='Gui/icon/hero.png' then return {kind='atlas',image=object,quad=atlasQuad,frame={w=50,h=30,source_w=70,source_h=50,offset_x=0,offset_y=0}} end
 end,small={}}
sceneView.draw(scene,ctx)
assert(rects>0 and prints>0 and drawn==2 and atlasDraws==1)
local entry,num=sceneView.inspect(scene)
assert(num==4 and entry.node.class=='Node')
sceneView.next(scene,1)
assert(sceneView.inspect(scene).node.class=='ImageView')
sceneView.next(scene,1)
assert(sceneView.inspect(scene).node.props.name=='AtlasImage')
sceneView.toggleGuides();sceneView.toggleHidden()
sceneView.draw(scene,ctx)
assert(sceneView.inspect(scene).node.props.name=='AtlasImage')
local selected=sceneView.pick(scene,ctx.x+ctx.w/2,ctx.y+100)
assert(type(selected)=='boolean')
sceneView.toggleText()
sceneView.reset()
assert(sceneView.inspect(scene).node.class=='Node')
print('Testes scene_view: OK')
