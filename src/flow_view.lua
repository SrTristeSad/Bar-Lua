-- Fase 12: visualização SOMENTE LEITURA de metadados de instruções ARM64.
-- A lista de chamadas NÃO representa ordem temporal, execução nem algoritmo.
local M = {}

function M.rows(entry)
    if type(entry) ~= 'table' then return {} end
    local rows = {}
    for _, item in ipairs(entry.calls or {}) do
        if type(item) == 'table' and type(item.name) == 'string' then
            rows[#rows + 1] = {
                name = item.name, count = tonumber(item.count) or 0,
                address = item.address or '?', external = item.external == true,
            }
        end
    end
    return rows
end

function M.draw(entry, panel)
    local x, y, w, h = panel.x, panel.y, panel.w, panel.h
    panel.background(x, y, w, h, {0.12, 0.16, 0.20})
    if not entry then
        panel.put('Sem relatório ARM64. Execute tools/analisar_fluxo.py conforme README.',
                  x + 16, y + 22, {1, 0.8, 0.4}, panel.small)
        return
    end
    panel.put(entry.name or '?', x + 14, y + 16, {1, 1, 1}, panel.small)
    panel.put(string.format('%s  |  %d B  |  %d instruções', entry.address or '?',
        entry.bytes or 0, entry.instructions or 0), x+14, y+41,
        {0.79, 0.90, 0.98}, panel.small)
    panel.put(string.format('Chamadas BL: %d  |  BLR: %d  |  desvios: %d  |  comparações: %d',
        entry.direct or 0, entry.indirect or 0, entry.branches or 0,
        entry.comparisons or 0), x+14,y+65,{0.82,0.91,0.95},panel.small)
    panel.put('Alvos estáticos (não comprovam execução, frequência ou semântica):',
        x+14,y+97,{1,0.80,0.49},panel.small)
    local rows = M.rows(entry)
    local lineHeight, initial = 24, y + 128
    local visible = math.max(0, math.floor((h - 185) / lineHeight))
    love.graphics.setScissor(x, initial, w, math.max(0, h - 176))
    for i=1, math.min(visible,#rows) do
        local target = rows[i]
        local label = string.format('%dx  %s', target.count, target.name)
        local maxChars = math.max(14, math.floor((w-35)/7.3))
        if #label > maxChars then label=label:sub(1,maxChars-3)..'...' end
        panel.put(label,x+16,initial+(i-1)*lineHeight,
                  target.external and {0.80,0.90,1.0} or {0.89,0.94,0.91},panel.small)
    end
    love.graphics.setScissor()
    panel.put('Somente metadados do ELF original; nenhum código Android é executado.',
        x+14,y+h-38,{0.73,0.83,0.90},panel.small)
end
return M