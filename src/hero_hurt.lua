-- F25: modelo ISOLADO do ramo Hero::addHurtFromEnemy para herói ainda vivo.
-- Não aplica dano na cena. Não simula callbacks, eventos nem pontuação reais.
local M = {}
local MAX = 2147483647
local function positive_integer(x)
    return type(x) == 'number' and x == math.floor(x) and x >= 0 and x <= MAX
end

--- @param hp number inteiro [1, 2^31-1], herói ainda vivo
--- @param damage number inteiro [0, 2^31-1], quantidade já calculada pelo jogo
--- @param attacker_key number|nil opcional apenas para identificação em pesquisa
--- @return table|nil, string|nil  Resultado puro, nunca escreve no jogo.
function M.simulate_alive(hp, damage, attacker_key)
    if not positive_integer(hp) or hp < 1 then
        return nil, 'HP inicial precisa ser inteiro positivo (herói vivo)'
    end
    if not positive_integer(damage) then
        return nil, 'dano precisa ser inteiro não negativo'
    end
    if attacker_key ~= nil and (type(attacker_key) ~= 'number' or attacker_key ~= math.floor(attacker_key) or attacker_key < -2147483648 or attacker_key > MAX) then
        return nil, 'identificador de atacante inválido'
    end
    local credited = math.min(hp, damage)
    local after = hp - credited
    local fatal = after == 0
    return {
        hp_before = hp,
        hp_after = after,
        incoming_damage = damage,
        accounted_damage = credited,
        lethal_branch = fatal,
        recorded_attacker_key = fatal and attacker_key or nil,
        -- Only reports whether the native virtual callback branch is reached.
        virtual_callback_branch = fatal,
        -- Cannot resolve BattleDataManager, attacker entity, or LogicEventSet here.
        native_events_executed = false,
    }
end

return M
