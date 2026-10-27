package.path = './?.lua;./?/init.lua;' .. package.path
local calls={draw=0,line=0,rectangle=0,matrix=nil}
local g={}
for _,n in ipairs({'setColor','setScissor','push','pop','translate','scale','setLineWidth','applyTransform'}) do g[n]=function() end end
g.draw=function() calls.draw=calls.draw+1 end
g.rectangle=function() calls.rectangle=calls.rectangle+1 end
g.line=function() calls.line=calls.line+1 end
love={graphics=g,math={newTransform=function()
 return {setMatrix=function(self,a,b,c,d,tx,ty) calls.matrix={a,b,c,d,tx,ty} end}
end}}
local view=require('src.animation_view')
local atlas={path='actors/example.bplist',image='sample.png',frames={{name='sprite.png',x=0,y=0,w=20,h=12,source_w=32,source_h=30}}}
local asset={path='actors/one.bexportjson',atlas_files={'example.plist'},
 armatures={{name='actor',bones={{name='root',parent='',layer_order=1,initial_display=0,displays={'sprite.png'},bind={x=0,y=0,scale_x=1,scale_y=1}}}}},
 animations={{name='actor',movements={{name='walk',duration=10,tracks={{bone='root',keys={
 {at=0,x=0,y=0,scale_x=1,scale_y=1,display_index=0},
 {at=5,x=10,y=0,scale_x=1,scale_y=1,display_index=0}}}}}}}}}
local ctx={x=0,y=0,w=600,h=420,put=function() end,background=function() end,imageFor=function() return 'tex' end,spriteQuad=function() return 'quad' end,small='font'}
view.reset();view.running=false;view.draw(asset,{atlas},ctx)
calls.draw=0;view.time=2.5;view.draw(asset,{atlas},ctx)
assert(calls.draw==1 and math.abs(calls.matrix[5]-5)<1e-6,'interpolação fracionária')
view.toggleGuides();view.draw(asset,{atlas},ctx)
assert(calls.line==2 and calls.rectangle>=2,'guias de pivô')
view.toggleGuides()
print('Testes animation_view: OK')
