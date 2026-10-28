-- F41: inspeção da criação e atualização de funções sem execução de gameplay.
local M={}
local page=1
function M.reset() page=1 end
function M.keypressed(key)
  if key=='right' or key=='down' then page=page%4+1;return true end
  if key=='left' or key=='up' then page=(page+2)%4+1;return true end
  if key=='r' then M.reset();return true end
  return false
end
function M.snapshot(report)
  if type(report)~='table' or report.phase~=41 or report.gameplay_enabled~=false
    or report.verified~=true or report.damage_chain_verified~=false
    or report.unmatched~=0 or report.basic_functions~=0 or report.selector_id~=10050 then
    return nil,'Relatório F41 ausente ou incompatível'
  end
  return {page=page,functions=report.functions,instructions=report.instructions,
    checks=report.checks,decoded=report.decoded,pending=report.pending,
    with_functions=report.with_functions,without_functions=report.without_functions,
    entries=report.entries,distinct=report.distinct,unmatched=report.unmatched,
    basic_id=report.basic_id,selector_id=report.selector_id,
    basic_functions=report.basic_functions,categories=report.categories}
end
function M.draw(report,panel)
  panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
  local function put(msg,dy,color)
    if dy>=0 and dy<panel.h-12 then
      panel.put(tostring(msg),panel.x+18,panel.y+dy,color or {0.90,0.94,0.97},panel.small)
    end
  end
  put('F41 | CSelfSkill: funções e ciclo de execução',20,{1,0.85,0.43})
  put('Inspeção nativa, sem aplicar golpes, efeitos ou dano.',50,{1,0.72,0.54})
  local r,err=M.snapshot(report)
  if not r then put(err,104,{1,0.52,0.50});return end
  put('Página '..r.page..'/4',101,{0.76,1,0.78})
  if r.page==1 then
    put(r.functions..' funções nativas | '..r.instructions..' instruções ARM64',149)
    put(r.checks..' verificações de instrução/endereço e símbolos.',187)
    put(r.decoded..' skills com listas lidas; '..r.pending..' pendentes.',226)
    put(r.entries..' referências de função | '..r.distinct..' IDs distintos.',268)
    put('IDs sem correspondência em tabela: '..r.unmatched,307,{0.72,1,0.75})
  elseif r.page==2 then
    put('HeroSkillConfig +0xE8 -> CSkill +0x38',152)
    put('CSelfSkill percorre a lista e chama AddFunction (vtable).',196)
    put('Init vincula criador, alvos e contexto a cada CFunction.',237)
    put('Update percorre funções e retira funções inativas.',278)
    put('NENHUMA dessas ações é executada nesta bancada.',324,{1,0.73,0.54})
  elseif r.page==3 then
    put('Ataque básico '..r.basic_id..' | seletor '..r.selector_id,152)
    put('Selector ID 10050 -> CSelfSkill.',193)
    put('Terceiro vetor: '..r.basic_functions..' IDs de CFunction.',232,{0.76,1,0.77})
    put('Dano direto por esse vetor: NÃO COMPROVADO.',276,{1,0.74,0.53})
    put('Outros caminhos nativos podem executar o ataque.',318)
  else
    put('Tipos mais frequentes no terceiro vetor:',148)
    for i,item in ipairs(r.categories or {}) do
      if i>8 then break end
      put(string.format('%-24s  %s ocorrências',item.name,item.count),165+i*28)
    end
  end
  put('Setas: páginas    R: reiniciar',panel.h-69)
  put('F41: pesquisa estática — não é combate jogável.',panel.h-40,{1,0.72,0.52})
end
return M
