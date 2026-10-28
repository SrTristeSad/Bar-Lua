package.path='./?.lua;./?/init.lua;'..package.path
local O=require('src.map_objects')
local map={objectgroups={{name='Original TMX',objects={
  {id=3,x=395,y=138,width=232,height=238,shape='rectangle',rotation=0},
  {id=4,x=10,y=40,width=20,height=20,shape='ellipse'},
  {id=5,x=2,y=2,width=0,height=40,shape='rectangle'},
  {id=6,x=1,y=1,width=10,height=10,shape='rectangle',rotation=30}
}}}}
local shapes=O.rectangles(map)
assert(#shapes==1 and shapes[1].id==3)
assert(O.overlaps(shapes[1], 512, 320, 18))
assert(not O.overlaps(shapes[1], 200, 200, 18))
assert(#O.rectangles({})==0)
print('F19 objetos TMX OK')
