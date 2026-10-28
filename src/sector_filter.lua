-- F34: replica predicados verificaveis do callback de selecao de setor.
-- Nao retorna alvo final: CCondition e outras etapas nao sao modeladas aqui.
local M={}
local function finite(x)
    return type(x)=='number' and x==x and x>-math.huge and x<math.huge
end
local function mask_valid(v)
    return finite(v) and v>=0 and v<=4294967295 and v==math.floor(v)
end
-- Intersecao bit-a-bit portavel entre LuaJIT e Lua 5.3 sem bitop global.
function M.mask_intersects(a,b)
    if not mask_valid(a) or not mask_valid(b) then return nil end
    while a>0 and b>0 do
        if a%2==1 and b%2==1 then return true end
        a=math.floor(a/2)
        b=math.floor(b/2)
    end
    return false
end
local function output(pass,stage,why,extra)
    local t={preselected=pass,final_target=nil,stage=stage,reason=why,
             post_conditions='not_evaluated'}
    if extra then for k,v in pairs(extra) do t[k]=v end end
    return t
end
-- Q: centro em coordenadas internas pre-divisao; radius, heading e width
-- da consulta do setor. C: entidade com userData, mascara e dimensoes virtuais
-- hipoteticas explicitamente fornecidas, nunca inferidas a partir do sprite.
function M.inspect(c,q)
    if type(c)~='table' or type(q)~='table' then return nil,'dados ausentes' end
    for _,v in ipairs({q.cx,q.cy,q.radius,q.heading,q.width,q.mask}) do
        if not finite(v) then return nil,'parametros invalidos' end
    end
    if q.radius<0 or not mask_valid(q.mask) or q.width~=math.floor(q.width) then
        return nil,'parametros invalidos'
    end
    if not c.userData then return output(false,'fixture','sem Entity no body.userData') end
    if not mask_valid(c.mask) then return nil,'mascara da entidade invalida' end
    local intersect=M.mask_intersects(c.mask,q.mask)
    if not intersect then return output(false,'type_mask','mascaras sem intersecao') end
    if not (finite(c.x) and finite(c.y)) then return nil,'posicao da entidade invalida' end
    local dx,dy=c.x-q.cx,c.y-q.cy
    local d2=dx*dx+dy*dy
    if not finite(d2) then return nil,'distancia invalida' end
    local kind=c.shape
    if kind==3 then
        return output(true,'callback','tipo 3: insercao direta apos mascara', {type=3})
    end
    if kind==1 then
        if not finite(c.radius) or c.radius<0 then
            return nil,'raio virtual nao identificado'
        end
        if d2 >= (q.radius+c.radius)^2 then
            return output(false,'circle','fora do raio combinado')
        end
    elseif kind==2 then
        if not (finite(c.width) and finite(c.height)) or c.width<0 or c.height<0 then
            return nil,'dimensoes virtuais nao identificadas'
        end
        if math.abs(dx)>q.radius+c.width/2 or math.abs(dy)>q.radius+c.height/2 then
            return output(false,'rect','fora dos eixos expandidos')
        end
    else
        return output(false,'shape','tipo de entidade nao suportado')
    end
    -- O executavel compara 2*sqrt(d2) com a constante (~1e-4).
    local distance=math.sqrt(d2)
    if 2*distance < (q.epsilon or 0.0001) then
        return output(false,'sector','vetor muito pequeno para definir direcao')
    end
    local angle=math.rad(q.heading)
    local cosv,sinv=math.cos(angle),math.sin(angle)
    local cosine=(dx*cosv+dy*sinv)/distance
    -- Evita NaN devido ao arredondamento do produto escalar.
    cosine=math.max(-1,math.min(1,cosine))
    local angle_deg=math.deg(math.acos(cosine))
    local half=math.floor(math.abs(q.width)/2)
    if q.width<0 then half=-half end  -- truncamento ARM64 para negativos
    if angle_deg>=half then
        return output(false,'sector','fora do angulo do setor',{angle=angle_deg,halfwidth=half})
    end
    return output(true,'callback','candidato do setor (condicoes pendentes)',
                  {angle=angle_deg,halfwidth=half,type=kind})
end
return M
