-- F29/F30/F31: catalogo original com identificacao de HP e velocidade-base.
-- Todos os demais atributos permanecem numericos e sem nomes inventados.
local values = require('src.level_attributes')
local schema = require('src.hero_schema')
local M = {level=1, showTypes=false, typePage=1}
local PER_PAGE = 11

function M.keypressed(key)
    if key == 't' then M.showTypes = not M.showTypes; return true end
    if key == 'left' then
        if M.showTypes then M.typePage = math.max(1, M.typePage - 1)
        else M.level = math.max(1, M.level - 1) end
        return true
    end
    if key == 'right' then
        if M.showTypes then M.typePage = math.min(3, M.typePage + 1)
        else M.level = math.min(100, M.level + 1) end
        return true
    end
    if key == 'r' then M.level=1; M.typePage=1; M.showTypes=false; return true end
    return false
end

function M.draw(group, report, panel, fieldReport, semanticReport)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function line(str,y,color)
        if y > panel.h-26 then return end
        panel.put(str,panel.x+14,panel.y+y,color or {0.88,0.92,0.96},panel.small)
    end
    line('FASE 31 | HeroConfig: HP e velocidade-base / ARM64 (1.0.1811)',12,{1,0.84,0.47})
    line('T: alternar Niveis / ValueType  |  setas: navegar  |  R: reiniciar',40)
    if M.showTypes then
        if not fieldReport or not schema.validatedHpTypes(fieldReport) then
            line('Relatorio F30 indisponivel ou inconsistente: execute analisar_esquema_heroi.py',77)
            return
        end
        line('Dispatch Hero::getValueByType  |  pagina '..M.typePage..'/3',84,{1,0.84,0.47})
        line('Codigo  offset Hero   comportamento observado',120)
        local first=(M.typePage-1)*PER_PAGE+1
        for idx=first,math.min(first+PER_PAGE-1,#fieldReport.value_types) do
            local info=fieldReport.value_types[idx]
            if info then
                local meaning=(info.id==5 and 'HP atual') or (info.id==11 and 'HP referencia') or (info.id==19 and 'velocidade-base') or
                    (info.kind=='delegate_entity' and 'encaminha para Entity') or
                    (info.kind=='derived_value' and 'valor calculado') or 'campo nao nomeado'
                line(string.format('%2d      %-8s      %s',info.id,info.offset or '--',meaning),153+(idx-first)*30)
            end
        end
        line('Comprovados: ValueType 5 (HP), 11 (HP ref.) e 19 (velocidade).',520,{1,0.74,0.57})
        return
    end
    if not group or not group.levels or #group.levels==0 then
        line('Catalogo privado ausente: execute tools/catalogar_niveis.py',77)
        return
    end
    local total=#group.levels
    local at=math.min(M.level,total)
    local row=group.levels[at]
    line('Hero: '..tostring(group.name)..' | entidade: '..tostring(group.entity_id),75)
    line('Config base: '..tostring(group.base_id)..' | niveis recuperados: '..total,102)
    line('Nivel '..at..' | Config ID '..row.id,130)
    line('Slot HeroConfig       valor bruto        diferenca         interpretacao',157,{1,0.84,0.47})
    local diff=at>1 and values.diff(group,at-1,at) or nil
    for index,slot in ipairs(values.slots) do
        local v=row.values[slot]
        local change=diff and diff[slot] or nil
        local meaning=schema.slotLabel(slot)
        line(string.format('%s                    %-7s         %-8s        %s',
            slot,tostring(v),change and string.format('%+d',change) or '---',meaning),182+(index-1)*30)
    end
    local hp=schema.configHp(row)
    if hp then line('HP na configuracao: '..hp..' | estado: Hero+0x314 | referencia: Hero+0x310',442,{0.74,1,0.80}) end
    local speed=schema.configSpeed(row)
    local component=schema.speedComponent(row,semanticReport)
    if component and fieldReport and schema.validatedSpeedType(fieldReport) then
        line(string.format('Velocidade-base: %d / 100 = %.2f (componente condicional)',speed,component),466,{0.74,1,0.80})
        line('ValueType 5: HP atual | 11: HP referencia | 19: velocidade',491)
    elseif fieldReport and schema.validatedHpTypes(fieldReport) then
        line('ValueType 5: HP atual | 11: HP referencia | F31 sem validacao',470)
    else
        line('Relatorios nativos F30/F31 indisponiveis.',470)
    end
    if report and report.total_instructions then
        line('F29: '..report.total_instructions..' | F31: '..tostring(semanticReport and semanticReport.verified_instruction_count or '?')..' instrucoes',520)
    end
    line('Seis slots permanecem sem nome; nao altera a cena ou a fisica.',532,{1,0.74,0.57})
end
return M
