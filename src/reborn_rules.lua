-- F27: visualização determinística das condições de Hero::update 1.0.1811.
-- Apenas avaliação estática de condições; NÃO altera vida, posição, skills ou mundo.
local M={}
local MAX=2147483647
local function integer(n)
    return type(n)=='number' and n==math.floor(n) and n>=0 and n<=MAX
end

--- Avalia independentemente dois pontos de Hero::update.
--- `clock` e `last_tick` são contadores NATIVOS abstratos, não segundos.
--- A operação real é subtração de inteiros ARM64 de 32 bits; esta prévia se
--- limita a valores crescentes sem overflow ou retorno de relógio.
function M.inspect(flag, last_tick, clock, battle_enabled)
    if flag~=0 and flag~=1 then return nil,'flag onDied deve ser 0 ou 1' end
    if type(battle_enabled)~='boolean' then return nil,'battle_enabled deve ser booleano' end
    if last_tick~=-1 and not integer(last_tick) then
        return nil,'marco anterior deve ser -1 ou inteiro nao negativo <= 2147483647'
    end
    if not integer(clock) then return nil,'clock deve ser inteiro nao negativo <= 2147483647' end
    if last_tick~=-1 and clock<last_tick then return nil,'marco decrescente: wraparound desconhecido' end
    local delta
    if last_tick~=-1 then delta=clock-last_tick end
    return {
        death_flag_set=(flag~=0),
        update_calls_die_logic=(flag~=0),
        update_calls_reborn=(delta~=nil and battle_enabled and delta>=1050),
        reborn_bool_argument=true,
        delta_raw=delta,
        threshold_raw=1050,
        proof='Hero::update virtual slots +0x98 and +0x50; ELF 1.0.1811',
        is_simulation=false,
        native_side_effects_executed=false,
        timer_unit_known=false,
    }
end
return M
