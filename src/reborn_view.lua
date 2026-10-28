-- F27: mostra provas do ciclo de morte/renascimento; sem executar reborn.
local rules=require('src.reborn_rules')
local M={clock=1120,last=0,flag=1,battle=true}
function M.keypressed(key)
    if key=='left' then M.clock=math.max(M.last, M.clock-10); return true end
    if key=='right' then M.clock=math.min(4000,M.clock+10); return true end
    if key=='up' then M.flag=1-M.flag; return true end
    if key=='down' then M.battle=not M.battle; return true end
    if key=='r' then M.clock,M.last,M.flag,M.battle=1120,0,1,true; return true end
    return false
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.13,0.17,0.20})
    local function line(s,y,color)
        if y>panel.h-30 then return end
        panel.put(s,panel.x+16,panel.y+y,color or {0.85,0.91,0.95},panel.small)
    end
    line('FASE 27 | Hero::update / Hero::reborn (ARM64)',14,{1,0.83,0.47})
    if type(report)~='table' or not report.total_instructions then
        line('Relatório indisponível. Execute tools/analisar_renascimento.py',52)
        return
    end
    line('BarbarQ 1.0.1811 | análise estática com SHA-256 verificado',52)
    line(string.format('%d instruções / %d checkpoints',report.total_instructions,report.total_checks),80)
    line('Golpe fatal -> onDied (+0x1bc = 1)',118,{0.68,1,0.75})
    line('Hero::update -> flag +0x1bc -> dieLogic (+0x98)',146)
    line('Hero::update -> condição separada -> reborn(true) (+0x50)',174)
    line('Hero::reborn -> resetReviveData -> player live / eventos',202)
    line('resetReviveData(true) usa spawn aleatório e SetTransform',230)
    local preview=assert(rules.inspect(M.flag,M.last,M.clock,M.battle))
    line('PRÉVIA DAS CONDIÇÕES NATIVAS (não executa jogabilidade):',274,{1,0.83,0.47})
    line(string.format('Flag: %d | BattleManager: %s | contador: %d',M.flag,tostring(M.battle),M.clock),304)
    line('Delta desde marco 0: '..tostring(preview.delta_raw)..' (limiar bruto: 1050)',334)
    line('dieLogic solicitado? '..tostring(preview.update_calls_die_logic),362)
    line('reborn(true) solicitado? '..tostring(preview.update_calls_reborn),390)
    line('Setas esq/dir = contador | cima = flag | baixo = modo | R = reiniciar',430)
    line('1050 NÃO é duração em segundos; unidade/agenda ainda não provadas.',466,{1,0.75,0.54})
    line('Não cria herói, HP, animação, respawn ou eventos.',494,{1,0.75,0.54})
end
return M
