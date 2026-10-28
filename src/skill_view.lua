-- Fase 21: catálogo de vínculos de botões para IDs de habilidades do APK.
-- NÃO executa habilidade, dano, alcance, hitboxes nem cooldown.
local M = {}

function M.display(row)
    if not row or type(row.id) ~= 'number' or type(row.skill_id) ~= 'number' then
        return nil
    end
    return {
        title = 'Configuração de vínculo #'..row.id,
        name = row.name or '',
        type = row.kind,
        button = row.button,
        skill_id = row.skill_id,
        skill_name = row.skill_name or '',
    }
end

function M.trace(trace, skill_id)
    if type(trace) ~= "table" or type(skill_id) ~= "number" then return nil end
    return trace[skill_id]
end

function M.draw(row, panel, counts, traces)
    local x,y,w,h = panel.x,panel.y,panel.w,panel.h
    panel.background(x,y,w,h,{0.12,0.16,0.20})
    local function put(value,dy,color)
        if dy >= 0 and dy < h-15 then
            panel.put(tostring(value),x+18,y+dy,color,panel.small)
        end
    end
    put('Fase 22 • rastreamento de IDs de habilidade',20,{1,0.86,0.50})
    put('Dados recuperados de config.skill.functionbindskill / heroskillconfig',52)
    if not row then
        put('Gere o catálogo local: python tools/catalogar_habilidades.py',95,{1,0.76,0.60})
        return
    end
    local d = M.display(row)
    if not d then
        put('Entrada inválida no catálogo local',95,{1,0.65,0.60})
        return
    end
    put(d.title,105,{0.75,0.90,1})
    put('Descrição original: '..d.name,145)
    put('Código de tipo: '..tostring(d.type)..'    Código de botão: '..tostring(d.button),195)
    put('ID da habilidade referenciada: '..d.skill_id,235,{0.67,1,0.75})
    put('Descrição da habilidade: '..d.skill_name,275)
    if counts then
        put('Total de vínculos: '..(counts.functionbindskill or 0),328)
        put('Configurações de habilidades: '..(counts.heroskillconfig or 0),355)
        put('Funções de dano descritas: '..(counts.functiondamage or 0),382)
    end
    local trace = M.trace(traces, d.skill_id)
    if trace then
        put('ID em '..tostring(trace.table)..': entradas='..trace.incoming_total..'  saídas='..trace.outgoing_total,416,{0.76,0.94,1})
        local offset = 451
        for _,ref in ipairs(trace.incoming or {}) do
            if offset > h-115 then break end
            put('Recebe referência de: '..ref.table..' #'..ref.id,offset,{0.82,0.90,1})
            offset = offset + 25
        end
        for _,ref in ipairs(trace.outgoing or {}) do
            if offset > h-115 then break end
            put('Cita possivelmente: '..ref.table..' #'..ref.id,offset,{0.78,0.98,0.83})
            offset = offset + 25
        end
    else
        put('Gere o rastreador local: python tools/rastrear_habilidades.py',440,{1,0.76,0.60})
    end
    put('Tokens iguais nao provam execucao, dano ou selecao de alvo.',h-83,{1,0.78,0.55})
    put('Nenhuma habilidade é executada neste painel.',h-57,{1,0.78,0.55})
end

return M
