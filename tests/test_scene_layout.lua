package.path='./?.lua;./?/init.lua;'..package.path
local L=require('src.scene_layout')
local function near(x,y)assert(math.abs(x-y)<1e-6,tostring(x)..' ~= '..tostring(y)) end
local root={class='Node',props={position={0,0},size={200,100},anchor={0,0},scale={1,1},visible=true},children={
 {class='Button',props={name='front',position={50,30},size={30,20},anchor={0,0},scale={1,1},z=10},children={}},
 {class='Panel',props={name='back',position={40,20},size={40,30},anchor={0,0},scale={1,1},z=-2},children={
    {class='ImageView',props={name='nested',position={15,10},size={5,5},anchor={0.5,0.5},scale={2,2}},children={}}
 }}
}}
local entries=L.flatten({root=root})
assert(#entries==4)
assert(entries[2].node.props.name=='back' and entries[3].node.props.name=='nested')
near(entries[2].world[5],40); near(entries[2].world[6],20)
-- Retangulo ancorado no centro, tamanho 5x5 com escala 2 => 10x10.
near(entries[3].world[5],50);near(entries[3].world[6],25)
local cx,cy=L.transform(entries[3].world,2.5,2.5); near(cx,55);near(cy,30)
local invx,invy=L.inverse(entries[3].world,cx,cy);near(invx,2.5);near(invy,2.5)
-- z da frente vence o ancestral de z inferior em regiao sobreposta.
local idx=L.pick(entries,55,30)
assert(entries[idx].node.props.name=='front')
local r=L.flatten({root={class='Node',props={position={100,20},size={80,40},anchor={0.5,0.5},skew={90,90}},children={}}})[1]
-- Skew igual é rotacao, a origem local foi deslocada pela ancora.
local x,y=L.transform(r.world,40,20);near(x,100);near(y,20)
assert(L.inverse({0,0,0,0,0,0},1,2)==nil)
print('Testes scene_layout: OK')
