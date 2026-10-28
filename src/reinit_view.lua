-- F28: laboratório de incrementos de configuração. Não altera o herói.
local rules=require('src.reinit_rules')
local M={level=3,delta=10}
function M.keypressed(key)
    if key=='up' then M.level=math.min(10,M.level+1);return true end
    if key=='down' then M.level=math.max(1,M.level-1);return true end
    if key=='right' then M.delta=math.min(100,M.delta+1);return true end
    if key=='left' then M.delta=math.max(-100,M.delta-1);return true end
    if key=='r' then M.level,M.delta=3,10;return true end
    return false
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.13,0.17,0.20})
    local function line(s,y,color)
        if y>panel.h-25 then return end
        panel.put(s,panel.x+14,panel.y+y,color or {0.87,0.92,0.96},panel.small)
    end
    line('FASE 28 | Hero::reInit(int,bool) / ARM64',14,{1,0.83,0.47})
    if not report or not report.total_instructions then
        line('Relatório indisponível: execute tools/analisar_reinit.py',45)
        return
    end
    line('BarbarQ 1.0.1811 | dados da biblioteca original verificados',46)
    line(string.format('%d instruções | %d verificações | %d funções',
        report.total_instructions,report.total_checks,#report.functions),72)
    line('full=true: Hero::init + ReimportWithBringData',111,{0.73,0.98,0.77})
    line('full=false: setLevel + diferenças entre configurações',139)
    line('Regras dos IDs: base + (level-1) x 10000',167)
    local id=assert(rules.configId(201,M.level))
    line(string.format('EXEMPLO FICTÍCIO: base 201, nível %d => ID %d',M.level,id),210,{1,0.83,0.47})
    local old,new,entity={}, {}, {}
    for _,entry in ipairs(rules.fields) do
        old[entry[2]],new[entry[2]]=100,100+M.delta
        entity[entry[1]]=200
    end
    local newstate=assert(rules.applySimpleDelta(old,new,entity,
        {extra_204_active=false,nested_88_active=false}))
    line(string.format('EXEMPLO FICTÍCIO: atributo 0x314: 200 + (%d) = %d',
        M.delta,newstate['0x314']),246)
    line('Setas cima/baixo: nível | esquerda/direita: delta | R: reset',280)
    line('Outros campos confirmados:',323,{1,0.83,0.47})
    line('0xc0, 0x32c, 0x330, 0x310, 0x318, 0x328, 0x31c, 0x1b8',352)
    line('Listas: habilidades novas na config podem ser adicionadas.',390)
    line('PlayerRestartGame é uma rotina distinta de reborn.',420)
    line('ATENÇÃO: valores e campos não são estatísticas de uma partida.',461,{1,0.72,0.55})
    line('Não executa init, addSkill, eventos, HP ou respawn.',486,{1,0.72,0.55})
end
return M
