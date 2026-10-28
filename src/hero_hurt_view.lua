-- F25 read-only panel for verifiable HP subtraction branch.
local hurt = require('src.hero_hurt')
local M = { hp = 120, damage = 45 }
function M.keypressed(key)
    if key == 'left' then M.damage = math.max(0, M.damage - 5); return true end
    if key == 'right' then M.damage = math.min(300, M.damage + 5); return true end
    if key == 'up' then M.hp = math.min(300, M.hp + 10); return true end
    if key == 'down' then M.hp = math.max(1, M.hp - 10); return true end
    if key == 'r' then M.hp, M.damage = 120, 45; return true end
    return false
end
function M.draw(report, panel)
    panel.background(panel.x, panel.y, panel.w, panel.h, {0.13,0.17,0.20})
    local function line(txt, y, color)
        if y > panel.h-25 then return end
        panel.put(txt, panel.x+16, panel.y+y, color or {0.84,0.9,0.95},panel.small)
    end
    line('FASE 25 | Hero::addHurtFromEnemy — ramo de HP',16,{1,0.83,0.47})
    if type(report)~='table' or not report.total_instructions then
        line('Catálogo não encontrado. Rode tools/analisar_valores_vida.py',52)
        return
    end
    line('ELF: BarbarQ 1.0.1811 / libcocos2dcpp.so',54)
    line(string.format('ARM64: %d instruções, %d verificações',report.total_instructions,report.total_checks),82)
    line('Offset do HP: '..tostring(report.hp_offset)..' | último agressor: '..tostring(report.last_attacker_offset),116)
    line('Condição nativa: HP >= 1; novo = HP - dano',156,{0.68,1,0.74})
    line('Se novo <= 0: grava HP=0, marca agressor e chama rotina virtual.',184)
    line('O dano contabilizado limita-se ao HP anterior no ramo fatal.',212)
    local result = assert(hurt.simulate_alive(M.hp, M.damage, 42))
    line('EXEMPLO ARTIFICIAL (sem personagens reais):',256,{1,0.8,0.45})
    line(string.format('HP inicial: %d   |   dano fornecido: %d',M.hp,M.damage),290)
    line(string.format('HP restante: %d   |   dano contabilizado: %d',result.hp_after,result.accounted_damage),322)
    line('Ramo fatal: '..(result.lethal_branch and 'sim' or 'não'),354)
    line('Setas esquerda/direita: dano; cima/baixo: HP; R: reiniciar.',400)
    line('Não modifica a vida na cena controlável.',446,{1,0.75,0.54})
    line('Sem efeitos nativos, recompensa, respawn ou combate real.',474,{1,0.75,0.54})
    line('Habilidade 4010020 ainda sem vínculo comprovado à fórmula.',502,{1,0.75,0.54})
end
return M
