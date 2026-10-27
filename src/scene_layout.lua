-- Matematica de inspeção de hierarquias CSB, sem dependencias de LÖVE.
-- Ancora, escala, flip, skew e z local sao avaliados; resposta do Cocos
-- quanto a anchors de widgets responsivos ainda exige comparacao visual.
local M = {}
local function v(p, name, i, default)
    local t = p[name]
    return type(t)=='table' and type(t[i])=='number' and t[i] or default
end
local function eye() return {1,0,0,1,0,0} end
function M.mul(a,b)
    return {a[1]*b[1]+a[3]*b[2], a[2]*b[1]+a[4]*b[2],
        a[1]*b[3]+a[3]*b[4], a[2]*b[3]+a[4]*b[4],
        a[1]*b[5]+a[3]*b[6]+a[5], a[2]*b[5]+a[4]*b[6]+a[6]}
end
function M.transform(a,x,y) return a[1]*x+a[3]*y+a[5],a[2]*x+a[4]*y+a[6] end
function M.inverse(a,x,y)
    local det = a[1]*a[4]-a[2]*a[3]
    if math.abs(det)<1e-9 then return nil end
    x,y=x-a[5],y-a[6]
    return (a[4]*x-a[3]*y)/det,(-a[2]*x+a[1]*y)/det
end
function M.parameters(p)
    local x,y=v(p,'position',1,0),v(p,'position',2,0)
    local sx,sy=v(p,'scale',1,1),v(p,'scale',2,1)
    if p.flip_x then sx=-sx end
    if p.flip_y then sy=-sy end
    local kx,ky=v(p,'skew',1,0),v(p,'skew',2,0)
    -- Cocos skewX==skewY corresponde a rotacao. Para desigualdade,
    -- usar cisalhamento residual e registrar como aproximacao.
    local degrees=(kx+ky)/2
    local function tanClamp(deg)
        return math.tan(math.rad(math.max(-80, math.min(80,deg))))
    end
    local shearX,shearY=tanClamp(kx-degrees),tanClamp(ky-degrees)
    return x,y,sx,sy,math.rad(degrees),shearX,shearY
end
function M.localMatrix(p)
    local x,y,sx,sy,r,kx,ky=M.parameters(p)
    local c,s=math.cos(r),math.sin(r)
    local w,h=v(p,'size',1,0),v(p,'size',2,0)
    local ax,ay=v(p,'anchor',1,0.5),v(p,'anchor',2,0.5)
    local a,b,c0,d=(c-s*ky)*sx,(s+c*ky)*sx,(c*kx-s)*sy,(s*kx+c)*sy
    return {a,b,c0,d,x-a*ax*w-c0*ay*h,y-b*ax*w-d*ay*h}
end
local function ordered(children)
    local output={}
    for i,child in ipairs(children or {}) do output[i]={node=child,index=i} end
    table.sort(output,function(a,b)
        local za=(a.node.props or {}).z or 0
        local zb=(b.node.props or {}).z or 0
        if za==zb then return a.index<b.index end
        return za<zb
    end)
    return output
end
M.ordered=ordered
function M.flatten(scene)
    local nodes={}
    local function walk(node,parent,depth,visible,opacity)
        if depth>70 or #nodes>=12000 then return end
        local p=node.props or {}
        local world=M.mul(parent,M.localMatrix(p))
        local entry={node=node, world=world, depth=depth,
            visible=visible and p.visible~=false,
            opacity=opacity*(type(p.opacity)=='number' and math.max(0,math.min(255,p.opacity))/255 or 1),
            w=v(p,'size',1,0), h=v(p,'size',2,0)}
        nodes[#nodes+1]=entry
        for _,child in ipairs(ordered(node.children)) do
            walk(child.node,world,depth+1,entry.visible,entry.opacity)
        end
    end
    if scene and scene.root then walk(scene.root,eye(),0,true,1) end
    return nodes
end
function M.pick(nodes,x,y,showHidden)
    -- Retorna o elemento visivel mais alto, seguindo a ordem de desenho.
    for i=#nodes,1,-1 do
        local entry=nodes[i]
        if entry.w>0 and entry.h>0 and (entry.visible or showHidden) then
            local lx,ly=M.inverse(entry.world,x,y)
            if lx and lx>=0 and ly>=0 and lx<=entry.w and ly<=entry.h then return i end
        end
    end
end
return M
