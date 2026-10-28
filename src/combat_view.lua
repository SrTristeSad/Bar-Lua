-- Fase 23: visualização de evidências ELF, NÃO simulação de combate.
local M = {}

function M.details(item)
    if type(item) ~= 'table' or type(item.name) ~= 'string' then return nil end
    return {
        name = item.name,
        address = item.address or '?',
        instructions = item.instructions or 0,
        checks = item.checks or {},
    }
end

function M.draw(item, panel)
    local x, y, w, h = panel.x, panel.y, panel.w, panel.h
    panel.background(x, y, w, h, {0.12, 0.16, 0.20})
    local function line(t, dy, color)
        if dy >= 0 and dy < h - 22 then
            panel.put(t, x + 20, y + dy, color, panel.small)
        end
    end
    line('FASE 23  |  Combate: evidências recuperadas do ARM64', 18, {1,0.86,0.48})
    line('Somente leitura de funções; não ativa dano, IA ou hitboxes.', 52)
    local d = M.details(item)
    if not d then
        line('Sem relatório. Execute tools/analisar_combate.py com o APK original.', 94, {1,0.72,0.60})
        return
    end
    line('Função: '..d.name, 108, {0.74,0.92,1})
    line('Endereço virtual: '..d.address, 145)
    line('Instruções ARM64 verificadas: '..tostring(d.instructions), 177)
    line('Chamadas e verificações identificadas:', 225, {0.75,1,0.75})
    for i, check in ipairs(d.checks) do
        if 246 + i * 26 >= h - 95 then break end
        line('• '..check, 246 + i * 26)
    end
    line('Presença da chamada não garante execução em toda situação.', h-73, {1,0.78,0.53})
    line('Dano, alcance, alvos e recarga ainda NÃO reproduzidos.', h-48, {1,0.78,0.53})
end

return M
