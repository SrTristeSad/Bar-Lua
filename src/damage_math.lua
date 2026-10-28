-- Fase 24: somente o núcleo aritmético observado em GetDamageValue.
-- NÃO é a rotina completa de dano: faltam estados das entidades, modificadores,
-- distribuição do RNG, eventual arredondamento e vínculo com habilidades.
local M = {}

local function finite(x)
    return type(x) == 'number' and x == x and x > -math.huge and x < math.huge
end

--- Avalia os operadores identificados no ELF, SEM obter parâmetros do jogo.
--- roll é fornecido pelo chamador; o módulo NÃO chama RNG e NÃO altera HP.
--- fields A,B,C,D_percent,E,threshold são entradas de pesquisa, não dados de personagem.
function M.core(p, roll, ratio)
    if type(p) ~= 'table' or not finite(roll) then return nil, 'entrada inválida' end
    ratio = ratio or 100
    if not finite(ratio) or ratio <= 0 then return nil, 'divisor inválido' end
    for _, key in ipairs({'A', 'B', 'C', 'D_percent', 'E', 'threshold'}) do
        if not finite(p[key]) then return nil, 'parâmetro inválido: '..key end
    end
    -- fcvtzs w23, s11: conversão float -> inteiro com truncamento em direção a zero.
    -- Apenas valores dentro do domínio int32 conhecido são aceitos.
    if p.threshold < -2147483648 or p.threshold > 2147483647 then
        return nil, 'limite inteiro não representável'
    end
    local threshold = math.modf(p.threshold)
    local triggered = roll <= threshold
    local percentFactor = triggered and (p.D_percent / ratio) or 1
    local base = p.A - p.B * (1 - p.C / ratio)
    local value = base * percentFactor * (1 - p.E / ratio)
    if not finite(value) then return nil, 'resultado não finito' end
    return {partial=value, triggered=triggered, base=base, percent_factor=percentFactor}
end

return M
