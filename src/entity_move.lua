-- F14: modelo isolado de decisão baseado no ELF original.
-- NÃO atualiza um mundo Box2D nem tenta replicar colisões/contatos.
local M = {}
local constants = require('reports.entity_move')
local abs = math.abs
local function finite(n)
    return type(n) == 'number' and n == n and n ~= math.huge and n ~= -math.huge
end

function M.plan(state, dx, dy)
    assert(type(state) == 'table', 'state inválido')
    assert(finite(dx) and finite(dy), 'deslocamento deve ser finito')
    assert(finite(state.x) and finite(state.y), 'posição deve ser finita')
    assert(type(state.flags) == 'number' and state.flags >= 0 and state.flags < 65536
           and state.flags % 1 == 0, 'flags inválidas')
    assert(type(state.body_type) == 'number' and state.body_type % 1 == 0,
           'body_type inválido')
    local flag5 = math.floor(state.flags / 32) % 2 == 1
    local flag1 = math.floor(state.flags / 2) % 2 == 1
    local result = {kind = 'none', x = state.x, y = state.y,
                    flags = state.flags, dx = dx, dy = dy, angle = state.angle or 0}
    if flag5 then
        if state.body_type == 0 then
            result.reason = 'tipo de corpo zero: retorno antecipado'
            return result
        end
        result.kind = 'write_velocity'
        if dx*dx + dy*dy > 0 and not flag1 then
            result.flags = state.flags + 2  -- coloca bit 1, que estava desativado
            result.clear_timer = true
        end
        result.reason = 'escrita direta dos componentes no corpo'
        return result
    end
    -- Comparação estrita reproduz o ramo observado em Entity::move.
    if dx > constants.epsilon_negative and dx < constants.epsilon_positive
       and dy > constants.epsilon_negative and dy < constants.epsilon_positive then
        result.reason = 'ambos componentes dentro do intervalo morto'
        return result
    end
    result.kind = 'set_transform'
    result.x = state.x + dx / constants.transform_divisor
    result.y = state.y + dy / constants.transform_divisor
    result.reason = 'destino da chamada Box2D SetTransform; colisões NÃO executadas'
    return result
end
return M
