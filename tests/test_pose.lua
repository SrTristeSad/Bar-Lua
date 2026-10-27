package.path = './?.lua;./?/init.lua;' .. package.path
local pose = require('src.pose')
local function eq(a, b, hint)
  assert(math.abs(a - b) < 1e-5, tostring(hint or '') .. ': ' .. tostring(a) .. ' ~= ' .. tostring(b))
end
local keys = {
  {at=0,x=0,y=0,scale_x=1,scale_y=1,skew_x=0,skew_y=0},
  {at=10,x=20,y=40,scale_x=3,scale_y=2,skew_x=math.pi,skew_y=0}
}
eq(pose.sample(keys, 5, true).x, 10, 'x interpolado')
eq(pose.sample(keys, 5, true).scale_x, 2, 'escala interpolada')
eq(pose.sample(keys, 5, false).x, 0, 'discreto')
eq(pose.sample(keys, 12, true).x, 20, 'último quadro')
eq(pose.sample(keys, -1, true).x, 0, 'primeiro quadro')
eq(pose.sample({keys[1], keys[1], keys[2]}, 0, true).x, 0, 'duplicata')
local m = pose.affine({x=3,y=4,scale_x=2,scale_y=3,skew_x=0,skew_y=0})
local x,y = pose.apply(m, 2,1)
eq(x,7,'matriz x');eq(y,7,'matriz y')
local parent = pose.affine({x=5,y=0,scale_x=2,scale_y=2})
local child = pose.affine({x=3,y=1,scale_x=1,scale_y=1})
x,y=pose.apply(pose.multiply(parent,child),0,0)
eq(x,11,'composição x');eq(y,2,'composição y')
local bones = {bones = {
 {name='root',parent='',bind={x=10,y=5},displays={'root.png'}},
 {name='child',parent='root',bind={x=2,y=3},displays={'child.png'}},
}}
local anim = {tracks={{bone='child',keys={{at=0,x=1,y=2,scale_x=1,scale_y=1}}}}}
local computed = pose.evaluate(bones,anim,0,true,true)
eq(computed[1].matrix.tx,10,'raiz');eq(computed[2].matrix.tx,13,'filho x')
eq(computed[2].matrix.ty,10,'filho y')
local without = pose.evaluate(bones,anim,0,true,false)
eq(without[2].matrix.tx,1,'base desligada')
local missing = pose.evaluate({bones={{name='alone',parent='absent'}}}, {tracks={}}, 0,true,true)
assert(missing[1].matrix, 'sem pai válido não pode travar')
local circular = pose.evaluate({bones={{name='a',parent='b'},{name='b',parent='a'}}}, {tracks={}},0,true,true)
assert(circular[1].matrix and circular[2].matrix, 'ciclo deve ser tratado sem recursão infinita')
print('Testes pose: OK')
