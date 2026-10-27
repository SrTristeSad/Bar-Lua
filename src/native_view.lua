-- Fase 11: consulta de metadados de símbolos ELF, sem executar bibliotecas ARM64.
local M = {}

function M.entries(class)
    local result = {}
    if type(class) ~= 'table' then return result end
    for _, method in ipairs(class.methods or {}) do
        if type(method) == 'table' and type(method.signature) == 'string' then
            result[#result+1] = string.format('%s | %s | %d B',
                method.address or '?', method.signature, method.bytes or 0)
        end
    end
    return result
end

function M.draw(class, panel)
    local x, y, w, h = panel.x, panel.y, panel.w, panel.h
    panel.background(x, y, w, h, {0.13, 0.17, 0.21})
    if not class then
        panel.put('Sem relatório ELF. Consulte tools/auditar_elf.py no README.', x+18, y+25,
            {1,0.82,0.4}, panel.small)
        return
    end
    panel.put('Auditoria ELF ARM64: ' .. (class.name or '?'),x+14,y+18,{1,1,1},panel.small)
    panel.put(tostring(class.count or 0)..' métodos exportados; amostra priorizada abaixo.',
        x+14,y+42,{0.70,0.86,0.98},panel.small)
    panel.put('Endereço virtual no ELF; NÃO é código Lua nem comportamento reconstruído.',
        x+14,y+66,{1,0.78,0.40},panel.small)
    love.graphics.setScissor(x,y+90,w,math.max(0,h-145))
    for index, method in ipairs(M.entries(class)) do
        local label = method
        -- Preserva o endereço e o começo da assinatura.
        local maxLen = math.max(32, math.floor((w - 30) / 7.5))
        if #label > maxLen then label = label:sub(1,maxLen-1)..'…' end
        panel.put(label,x+16,y+101+(index-1)*28,{0.86,0.93,0.95},panel.small)
    end
    love.graphics.setScissor()
    panel.put('Fontes: .dynsym / readelf / c++filt. Nenhuma biblioteca Android é executada.',
        x+14,y+h-37,{0.74,0.84,0.90},panel.small)
end
return M
