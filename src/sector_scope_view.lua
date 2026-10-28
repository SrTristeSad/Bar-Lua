-- F33: bancada somente de consulta para a regiao de busca AABB dos seletores.
local scope=require('src.sector_scope')
local M={}
local base,angle=76,0

function M.reset()
    base,angle=76,0
end
function M.keypressed(key)
    if key=='left' then base=math.max(0,base-1);return true end
    if key=='right' then base=math.min(10000,base+1);return true end
    if key=='up' then angle=(angle+15)%360;return true end
    if key=='down' then angle=(angle-15)%360;return true end
    if key=='r' then M.reset();return true end
    return false
end
function M.snapshot(report)
    local bounds,err=scope.inspect(report,base,angle)
    return bounds and {radius=base,angle=angle,bounds=bounds,
        sectors=report.sector_records,using_type3=report.scope3_count,
        with_simple_param=report.scope3_with_simple_parameter} or nil,err
end
function M.draw(report,panel)
    local x,y,w,h=panel.x,panel.y,panel.w,panel.h
    panel.background(x,y,w,h,{0.12,0.16,0.20})
    local function put(t,dy,color)
        if dy>=0 and dy<h-15 then panel.put(t,x+20,y+dy,color or {0.91,0.93,0.97},panel.small) end
    end
    put('FASE 33  |  Alcance -> ValueType 3 -> QueryAABB',18,{1,0.84,0.42})
    put('Inspecao de geometria de busca; NAO e hitbox de dano.',53,{1,0.74,0.52})
    local state,err=M.snapshot(report)
    if not state then put(err or 'Relatorio F33 ausente',98,{1,0.5,0.42});return end
    put(string.format('Tabela original: %d setores; %d usam ValueType 3',state.sectors,state.using_type3),96)
    put('Seletor de exemplo: 10052, fator 100%, operacao ausente',123)
    put('Config barbaro nivel 1: alcance bruto 76 (ajustavel nesta tela)',150)
    put(string.format('Valor de teste: %d   Direcao hipotetica: %d graus',base,angle),178,{0.78,1,0.78})
    local b=state.bounds
    put(string.format('AABB Box2D: (%.2f, %.2f) a (%.2f, %.2f)',b.minx,b.miny,b.maxx,b.maxy),210)
    put('Centro de demonstracao: (200,150), deslocamento zero',237)
    local dim=math.min(w-65,math.max(50,h-345),260)
    if dim>20 and love and love.graphics then
        local xx=x+(w-dim)*0.5
        local yy=y+265
        love.graphics.setColor(0.18,0.29,0.37,1)
        love.graphics.rectangle('fill',xx,yy,dim,dim)
        love.graphics.setColor(0.35,0.95,0.72,1)
        love.graphics.rectangle('line',xx+15,yy+15,dim-30,dim-30)
        love.graphics.line(xx+dim/2-8,yy+dim/2,xx+dim/2+8,yy+dim/2)
        love.graphics.line(xx+dim/2,yy+dim/2-8,xx+dim/2,yy+dim/2+8)
    end
    put('Esquerda/direita: variar alcance; cima/baixo: direcao; R: reiniciar',h-72)
    put('Busca AABB -> filtro posterior; NAO existe combate implementado.',h-45,{1,0.73,0.49})
end
return M
