-- F26: painel de pesquisa. O experimento numérico é deliberadamente isolado.
local rules=require('src.death_rules')
local M={current=240,old=120}
function M.keypressed(key)
    if key=='left' then M.current=math.max(M.old,M.current-10);return true end
    if key=='right' then M.current=math.min(2000,M.current+10);return true end
    if key=='up' then M.old=math.min(M.current,M.old+10);return true end
    if key=='down' then M.old=math.max(0,M.old-10);return true end
    if key=='r' then M.current,M.old=240,120;return true end
    return false
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.13,0.17,0.20})
    local function line(str,y,color)
        if y>panel.h-25 then return end
        panel.put(str,panel.x+16,panel.y+y,color or {0.84,0.9,0.95},panel.small)
    end
    line('FASE 26 | onDied != dieLogic',16,{1,0.83,0.47})
    if type(report)~='table' or not report.total_instructions then
        line('Relatório indisponível. Execute tools/analisar_morte.py',52)
        return
    end
    line('BarbarQ 1.0.1811 / libcocos2dcpp.so',52)
    line(string.format('%d instruções ARM64 | %d verificações',report.total_instructions,report.total_checks),80)
    line('Golpe fatal -> callback virtual +0x48 -> Entity::onDied',118,{0.68,1,0.74})
    line('Entity::onDied: marca byte +0x1bc = 1',146)
    line('Hero::dieLogic: outro slot virtual (+0x98)',174)
    line('dieLogic: estado, skills, KDA, pontuação e eventos',202)
    local result=assert(rules.score_preview(M.current,M.old))
    line('DEMONSTRAÇÃO NUMÉRICA ISOLADA (não é uma partida):',258,{1,0.8,0.45})
    line(string.format('Pontuação atual: %d    Antiga: %d',M.current,M.old),286)
    line('Perda = trunc((atual - antiga) x 0,75)',314)
    line(string.format('Perda: %d     Nova pontuação: %d',result.loss,result.score_after),342)
    line('Setas: ajustar pontos | R: restaurar',382)
    line('Ainda desconhecido: quem agenda dieLogic após onDied.',426,{1,0.75,0.54})
    line('Não executa callbacks, morte, IA, recompensas ou respawn.',454,{1,0.75,0.54})
end
return M
