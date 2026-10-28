-- F30: interpretacao SOMENTE dos campos comprovados no BarbarQ ARM64 1.0.1811.
-- Modulo de consulta: nao altera o heroi, nao executa dano ou revive.
local M = {}
M.hpSlot = '0x44'
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

function M.validatedHpTypes(catalog)
    local current = M.valueType(catalog, M.valueTypeHpCurrent)
    local reference = M.valueType(catalog, M.valueTypeHpReference)
    return current and current.offset == M.hpCurrent and
        reference and reference.offset == M.hpReference or false
end

return M
