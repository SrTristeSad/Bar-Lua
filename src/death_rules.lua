-- F26: modelo MATEMATICO e ISOLADO de uma parte de Hero::dieLogic.
-- Nenhuma rotina de jogo, pontuação real, respawn ou dano é executada.
local M = {}
local LIMIT = 2147483647
local function integer(x)
    return type(x)=='number' and x==math.floor(x) and x>=0 and x<=LIMIT
end

--- Representa SOMENTE a sequência scvtf; fmul(0.75); fcvtzs; sub.
--- old_score é o valor retornado por PlayerInfoManager::getPlayOldScoreByKey.
--- Não reivindica equivalência com regras de modo, KDA, kill ou respawn.
function M.score_preview(current_score, old_score)
    if not integer(current_score) or not integer(old_score) then
        return nil,'pontuações devem ser inteiros não negativos de 32 bits'
    end
    if old_score>current_score then
        return nil,'modelo restrito a pontuação anterior <= atual'
    end
    local difference=current_score-old_score
    -- F26: fcvtzs trunca em direção a zero. Somente valores positivos aqui.
    local loss=math.floor(difference * 0.75)
    local result=current_score-loss
    return {score_before=current_score,old_score=old_score,loss=loss,
            score_after=result,score_difference=difference,
            native_events_executed=false,death_logic_executed=false}
end

-- Ramo nativo verificado: onDied apenas grava um byte de sinalização.
-- Não confundir com a função virtual separada dieLogic.
function M.on_died_flag_preview()
    return {flag_offset='0x1bc',flag_value=1,
            callback='Entity::onDied',actual_death_logic_executed=false}
end
return M
