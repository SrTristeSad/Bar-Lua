-- Fase 24: laboratório em modo somente leitura (parâmetros apenas de EXEMPLO).
local mathCore = require('src.damage_math')
local M = {}
M.roll = 30
M.threshold = 30
function M.keypressed(key)
    if key == 'left' then M.roll = math.max(1, M.roll - 1); return true end
    if key == 'right' then M.roll = math.min(100, M.roll + 1); return true end
    if key == 'up' then M.threshold = math.min(100, M.threshold + 5); return true end
    if key == 'down' then M.threshold = math.max(0, M.threshold - 5); return true end
    return false
end
function M.draw(report, panel)
    panel.background(panel.x, panel.y, panel.w, panel.h, {0.13,0.17,0.20})
    local function line(txt, y, color)
        if y > panel.h - 28 then return end
        panel.put(txt, panel.x+16, panel.y+y, color or {0.85,0.91,0.96}, panel.small)
    end
    line('FASE 24 | Núcleo matemático de dano (PARCIAL)', 16, {1,0.87,0.49})
    if type(report) ~= 'table' or not report.ratio then
        line('Relatório não encontrado. Execute tools/analisar_formula_dano.py.',56)
        return
    end
    line('Proveniência: libcocos2dcpp.so / BarbarQ 1.0.1811', 54)
    line('Função: '..tostring(report.name),84)
    line('ARM64: '..tostring(report.instructions)..' instruções; '..tostring(report.checked)..' verificações.',112)
    line('DECIMAL_RATIO: '..tostring(report.ratio)..' (constante original)',142)
    line('Fórmula do ramo auditado:',182,{0.66,1,0.75})
    line('base = A - B*(1-C/100)',210)
    line('fator = (sorteio <= trunc(limite)) ? D/100 : 1',238)
    line('parcial = base * fator * (1-E/100)',266)
    line('Parâmetros: offsets 0x38 0x40 0x48 0x58 0x50 0x60',302)
    line('EXEMPLO ARTIFICIAL (não são valores do BarbarQ):',340,{1,0.80,0.44})
    local sample = {A=100, B=25, C=20, D_percent=150, E=10, threshold=M.threshold}
    local result = mathCore.core(sample, M.roll, report.ratio)
    line(string.format('A=100, B=25, C=20, D=150, E=10, limiar=%d', M.threshold),368)
    line(string.format('Sorteio fixo=%d | condição=%s | núcleo=%.3f', M.roll,
        result and (result.triggered and 'sim' or 'não') or '?', result and result.partial or 0),396)
    line('Setas esquerda/direita: sorteio; cima/baixo: limiar (apenas teste).',426)
    line('Não altera HP; sem hitboxes, alvos, recarga ou ataque em jogo.',466,{1,0.76,0.56})
    line('Outras condições e modificadores nativos ainda não reproduzidos.',494,{1,0.76,0.56})
end
return M
