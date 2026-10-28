package.path='./?.lua;./?/init.lua;'..package.path
local F=require('src.sector_filter')
local V=require('src.sector_filter_view')
local r=dofile('reports/sector_filter.lua')
assert(r.phase==34 and r.verified_instructions==396 and r.checkpoints==45)
assert(F.mask_intersects(2,1)==false)
assert(F.mask_intersects(3,1)==true)
assert(F.mask_intersects(0,0)==false)
assert(F.mask_intersects(2147483648,2147483648)==true)
assert(F.mask_intersects(-1,1)==nil)
local q={cx=0,cy=0,radius=76,heading=0,width=90,mask=1}
local function test(shape,x,y,extra)
    local candidate={userData=true,mask=1,shape=shape,x=x,y=y}
    if shape==1 then candidate.radius=0 end
    if shape==2 then candidate.width=0;candidate.height=0 end
    for k,v in pairs(extra or {}) do candidate[k]=v end
    local a,err=F.inspect(candidate,q)
    assert(a,err)
    assert(a.final_target==nil and a.post_conditions=='not_evaluated')
    return a
end
assert(test(1,60,0).preselected)
assert(not test(1,-60,0).preselected)
assert(not test(1,76,0).preselected) -- fronteira circular estrita
assert(test(1,75.9,0).preselected)
assert(not test(1,60,0,{mask=2}).preselected)
assert(not test(1,60,0,{userData=false}).preselected)
assert(not test(1,0,0).preselected)
assert(test(1,60,0.001).preselected)
assert(test(1,60,0,{radius=10}).preselected)
assert(not test(1,90,0,{radius=10}).preselected)
assert(not test(2,40,40).preselected) -- 45 graus exatamente meia abertura
assert(test(2,40,35).preselected)
assert(test(2,80,0,{width=8,height=8}).preselected)
assert(not test(2,81,0,{width=8,height=8}).preselected)
assert(test(3,-999,0).preselected) -- tipo 3 ignora setor
assert(not test(8,0,0).preselected)
assert(F.inspect({userData=true,mask=1,shape=1,x=20,y=0},q)==nil)
assert(F.inspect({userData=true,mask=1,shape=2,x=20,y=0},q)==nil)
assert(F.inspect({userData=true,mask=1,shape=1,x=20,y=0,radius=0}, {cx=0,cy=0,radius=-1,heading=0,width=90,mask=1})==nil)
V.reset()
local snap=V.snapshot(r)
assert(snap and snap.name=='Circulo na frente' and snap.result.preselected)
assert(V.keypressed('right'))
assert(not V.snapshot(r).result.preselected)
assert(V.keypressed('right'))
assert(V.snapshot(r).index==3)
assert(V.keypressed('r'))
assert(V.snapshot(r).index==1)
assert(V.snapshot({phase=33})==nil)
local calls={}
V.draw(r,{x=0,y=0,w=650,h=600,small={},background=function(...)end,put=function(s)calls[#calls+1]=s end})
assert(#calls>=8)
print('F34 SECTOR FILTER LUA OK')
