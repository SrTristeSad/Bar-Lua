-- F39: mostra evidencias estruturais, sem simular habilidades/dano.
local M={}
local index=1
function M.reset() index=1 end
function M.keypressed(key)
  if key=='right' or key=='down' then index=index%3+1;return true end
  if key=='left' or key=='up' then index=(index+1)%3+1;return true end
  if key=='r' then M.reset();return true end
  return false
end
function M.snapshot(report)
  if type(report)~='table' or report.phase~=39 or report.gameplay_enabled~=false
      or report.condition_lists_verified~=false then
    return nil,'Relatorio da F39 ausente ou incompatível'
  end
  local pages={'Carregador HeroSkillConfig','Habilidade básica 4010020','Ocorrências entre tabelas'}
  return {index=index,title=pages[index],skill_id=report.skill_id,
    instructions=report.instructions,checks=report.checks,
    count=report.record_count,occurrences=report.occurrences or {},
    tail=report.tail or {},fields=report.fields or {}}
end
function M.draw(report,panel)
  panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
  local function put(msg,dy,color)
    if dy>=0 and dy<panel.h-11 then
      panel.put(tostring(msg),panel.x+17,panel.y+dy,color or {0.9,0.94,0.97},panel.small)
    end
  end
  put('F39 | Esquema nativo de HeroSkillConfig',20,{1,0.83,0.43})
  put('Auditoria de dados, sem alterar o combate.',48,{1,0.76,0.55})
  local s,err=M.snapshot(report)
  if not s then put(err,106,{1,0.5,0.5});return end
  put('Painel '..s.index..'/3: '..s.title,105,{0.75,1,0.75})
  if index==1 then
    put('HeroSkillConfig::load  |  '..s.instructions..' instrucoes / '..s.checks..' checks',153)
    put('Carrega tres vetores: +0xB0  +0xD0  +0xE8',192)
    put('Objeto opcional: +0xA8 | pointer enhancement: +0x100',233)
    put('Os vetores ainda nao foram mapeados com seguranca',280,{1,0.75,0.5})
  elseif index==2 then
    put('Registro original da habilidade '..s.skill_id,155)
    put('Vinculo confirmado: botao 10039  | codigo 2',195)
    put('Ultimos tokens numericos: '..table.concat(s.tail,', '),235)
    put('Nao presumir que os dois zeros sejam listas vazias.',282,{1,0.77,0.51})
  else
    put('Total de registros de habilidade: '..s.count,154)
    put('Ocorrencias exatas do ID (sem confundir substrings):',194)
    for i,row in ipairs(s.occurrences) do
      put(row.table..' : '..row.count,203+i*33)
    end
    put('Ocorrencia textual nao prova chamada em runtime.',335,{1,0.76,0.5})
  end
  put('SEM hitbox, alvo, dano ou mudanca no jogo.',panel.h-89,{1,0.74,0.5})
  put('Setas: trocar tela   R: reiniciar',panel.h-54)
end
return M
