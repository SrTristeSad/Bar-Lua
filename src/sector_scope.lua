-- F33: modelo isolado da busca AABB inicial de CSelectTargetSector.
-- NÃO simula colisao, filtros de equipes, dano, setor efetivo ou hits.
local M = {}
local function finite(n)
    return type(n)=='number' and n==n and n>-math.huge and n<math.huge
end

-- Somente ValueType=3 sem objeto Operation; raw representa Hero+0x330.
function M.radius(raw, factor, operationAbsent)
    if not finite(raw) or raw<0 or not finite(factor) or factor<0 or not operationAbsent then
        return nil, 'parametro dinamico ou invalido'
    end
    return raw*(factor/100)
end

-- b2World::QueryAABB recebe caixa quadrada; os filtros do setor sao posteriores.
-- Coordenadas em unidades de Entity antes do divisor nativo 100.
function M.queryAABB(x,y,heading,offsetAngle,centerDistance,radius,divisor)
    if not (finite(x) and finite(y) and finite(heading) and finite(offsetAngle)
        and finite(centerDistance) and finite(radius) and radius>=0 and
        finite(divisor) and divisor>0) then
        return nil, 'argumentos invalidos'
    end
    local angle=math.rad(heading+offsetAngle)
    local cx=x+centerDistance*math.cos(angle)
    local cy=y+centerDistance*math.sin(angle)
    return {cx=cx,cy=cy,minx=(cx-radius)/divisor,miny=(cy-radius)/divisor,
            maxx=(cx+radius)/divisor,maxy=(cy+radius)/divisor}
end

function M.inspect(report,raw,heading)
    if type(report)~='table' or report.phase~=33 or report.scope_type~=3 or
        report.example_factor~=100 or report.query_aabb_divisor~=100 then
        return nil,'relatorio F33 indisponivel ou incompatível'
    end
    local radius,err=M.radius(raw,report.example_factor,true)
    if not radius then return nil,err end
    local bounds,reason=M.queryAABB(200,150,heading or 0,0,0,radius,report.query_aabb_divisor)
    if not bounds then return nil,reason end
    bounds.radius=radius
    return bounds
end
return M
