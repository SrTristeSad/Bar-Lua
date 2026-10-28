-- F30/F31: interpretacao SOMENTE dos campos comprovados no BarbarQ ARM64 1.0.1811.
-- Modulo de consulta: nao altera o heroi, nao executa dano ou revive.
local M = {}
M.hpSlot = '0x44'
M.speedSlot = '0x48'
M.damageSlot = '0x3c'
M.damageScopeSlot = '0x40'
M.damageHeroOffset = '0x32c'
M.damageScopeHeroOffset = '0x330'
M.valueTypeDamage = 2
M.valueTypeDamageScope = 3
M.speedHeroOffset = '0x328'
M.valueTypeSpeed = 19
M.hpCurrent = '0x314'
M.hpReference = '0x310'
M.valueTypeHpCurrent = 5
M.valueTypeHpReference = 11

function M.configHp(levelRow)
    if type(levelRow) ~= 'table' or type(levelRow.values) ~= 'table' then
        return nil, 'configuracao indisponivel'
    end
    local hp = levelRow.values[M.hpSlot]
    if type(hp) ~= 'number' or hp % 1 ~= 0 or hp < 0 then
        return nil, 'slot de HP ausente ou invalido'
    end
    return hp
end

function M.slotLabel(slot)
    if slot == M.hpSlot then return 'HP inicial' end
    if slot == M.speedSlot then return 'velocidade-base' end
    if slot == M.damageSlot then return 'dano-base' end
    if slot == M.damageScopeSlot then return 'alcance de dano (parametro)' end
    return 'atributo nao identificado'
end

function M.valueType(catalog, id)
    if type(catalog) ~= 'table' or type(catalog.value_types) ~= 'table'
        or type(id) ~= 'number' or id % 1 ~= 0 then
        return nil, 'catalogo ou codigo indisponivel'
    end
    for _, info in ipairs(catalog.value_types) do
        if info.id == id then return info end
    end
    return nil, 'codigo ValueType desconhecido'
end

function M.configSpeed(levelRow)
    if type(levelRow)~='table' or type(levelRow.values)~='table' then
        return nil, 'configuracao indisponivel'
    end
    local raw=levelRow.values[M.speedSlot]
    if type(raw)~='number' or raw%1~=0 or raw<0 then
        return nil, 'velocidade-base ausente ou invalida'
    end
    return raw
end

function M.validatedSpeedType(catalog)
    local speed=M.valueType(catalog,M.valueTypeSpeed)
    return speed and speed.offset==M.speedHeroOffset or false
end

function M.validatedSpeedReport(report)
    return type(report)=='table' and report.phase==31 and
        report.confirmed_speed_slot==M.speedSlot and
        report.speed_hero_offset==M.speedHeroOffset and
        report.speed_value_type==M.valueTypeSpeed and
        report.speed_divisor==100 or false
end

function M.speedComponent(levelRow,report)
    if not M.validatedSpeedReport(report) then
        return nil,'relatorio nativo de velocidade invalido'
    end
    local raw,err=M.configSpeed(levelRow)
    if not raw then return nil,err end
    return raw/report.speed_divisor
end

function M.validatedHpTypes(catalog)
    local current = M.valueType(catalog, M.valueTypeHpCurrent)
    local reference = M.valueType(catalog, M.valueTypeHpReference)
    return current and current.offset == M.hpCurrent and
        reference and reference.offset == M.hpReference or false
end

-- O significado desses setters e comprovado, mas o alcance nao tem unidade
-- conhecida; nao convertê-lo em raio ou usar para atingir alvos na cena.
local function rawCombat(levelRow, slot)
    if type(levelRow)~='table' or type(levelRow.values)~='table' then
        return nil,'configuracao indisponivel'
    end
    local v=levelRow.values[slot]
    if type(v)~='number' or v%1~=0 or v<0 then
        return nil,'parametro ausente ou invalido'
    end
    return v
end

function M.configDamage(levelRow)
    return rawCombat(levelRow,M.damageSlot)
end

function M.configDamageScope(levelRow)
    return rawCombat(levelRow,M.damageScopeSlot)
end

function M.validatedCombatTypes(catalog,report)
    if type(report)~='table' or report.phase~=32 or
        type(report.damage)~='table' or type(report.damage_scope)~='table' then
        return false
    end
    local a,b=M.valueType(catalog,M.valueTypeDamage),M.valueType(catalog,M.valueTypeDamageScope)
    return a and b and a.offset==M.damageHeroOffset and
       b.offset==M.damageScopeHeroOffset and
       report.damage.slot==M.damageSlot and
       report.damage.offset==M.damageHeroOffset and
       report.damage.value_type==M.valueTypeDamage and
       report.damage.setter=='Hero::setDamage(int)' and
       report.damage_scope.slot==M.damageScopeSlot and
       report.damage_scope.offset==M.damageScopeHeroOffset and
       report.damage_scope.value_type==M.valueTypeDamageScope and
       report.damage_scope.setter=='Hero::setDamageScope(int)' or false
end

return M
