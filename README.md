# Bar-Lua — BarbarQ 1.0.1811 no Windows (reconstrução fiel em Lua)

**Objetivo:** estudar um APK original do BarbarQ e reproduzir sua experiência no PC com **Lua e LÖVE2D**, sem emulador Android. Isto **não** é um jogo inspirado no BarbarQ. Os recursos recuperados servem de referência, mas portar a lógica original exige engenharia reversa adicional.

## Fase 26 — o callback `onDied` e a rotina `dieLogic` são distintos

**Nova evidência sobre morte (BarbarQ 1.0.1811).** Após `Hero::addHurtFromEnemy`
zerar o HP, a chamada virtual pelo offset `+0x48` aponta, pelas **relocações
originais da vtable** de `Hero`, para `Entity::onDied`, e **não** para
`Hero::dieLogic`. A rotina `Entity::onDied` apenas grava o byte de estado
`+0x1bc = 1`. O método `Hero::dieLogic` ocupa outro slot (`+0x98`) e
executa trabalho adicional; **a relação temporal entre os dois métodos
não foi comprovada**.

- O analisador `tools/analisar_morte.py` valida SHA-256, endereços e tamanhos dos
  símbolos, **29 checkpoints** de instruções em **4 funções/377 instruções**, e
  os endereços reais das relocações de vtable de `Hero` e `Entity`. Gera
  `reports/death_flow.json` e `reports/death_flow.lua`. Não desvia nem
  executa a biblioteca nativa.
- `Entity::dieLogic` limpa a cadeia de habilidades, adiciona um estado com
  código observado `8`, zera indicadores e chama a rotina que registra o
  jogador como não vivo.
- `Hero::dieLogic` invoca `Entity::dieLogic`, `CSkillRandom::OnHeroDie`, atualiza
  estatísticas e dispara um evento. Um núcleo matemático encontrado é
  `perda = trunc((score_atual - score_antigo) * 0.75)`, em que `trunc` é
  arredondamento **em direção a zero** na instrução `fcvtzs`. O escopo do
  simulador limita-se a inteiros não negativos com `score_antigo <= score_atual`.
- `src/death_rules.lua` reproduz **somente esse cálculo isolado** e o indicador
  de `onDied`. A aba **Morte** (`Ctrl+N`) permite alterar números hipotéticos
  sem alterar a cena controlável.
- A investigação ainda **não demonstra** quem agenda `dieLogic` após `onDied`,
  o momento da animação de morte, respawn ou as regras de recompensa. A fórmula
  de pontuação de um ramo não equivale a uma regra universal dos modos de jogo.

**Para validar:** use sua própria biblioteca Android extraída em
`lib/arm64-v8a/libcocos2dcpp.so` e execute
`python tools/analisar_morte.py`, seguido de
`python -m unittest discover -s tests -q`.

**Testes:** 102 testes automatizados aprovados. Execução gráfica do LÖVE2D
no Windows **ainda não foi testada**. Os recursos do APK continuam fora do
repositório público.

---

## Fase 22 — rastreamento de alvos e referências de habilidades (sem dano jogável)

O analisador `tools/rastrear_habilidades.py` indexa **72.765 registros** de 13 tabelas
originais, conferindo o SHA-256 das oito tabelas estudadas na Fase 21. Encontrou
**74.308 pares de IDs** via ocorrência de tokens numéricos completos entre registros.
**Essas ocorrências são candidatas de referência, NÃO necessariamente arestas de
execução.** Campos ainda não tiveram seus esquemas binários ou semântica de
execução reconstruídos.

- **Vínculo confirmado:** `functionbindskill` ID `10039` usa botão de código `2`
  e aponta para a configuração de habilidade `4010020` (ataque do bárbaro).
- A configuração `4010020` tem **uma referência de entrada** e **nenhuma saída
  identificável** nas tabelas auditadas. Não há ligação comprovada até uma
  fórmula de dano, um seletor de alvos, um hitbox ou um cooldown.
- A habilidade `4020020` contém menção ao seletor em setor `10052`, e o
  registro `functionrandomskill` `10070` menciona `4070020` e `4080020`.
  Isso **não prova** que o botão `10039` passa por esses registros.
- A aba **Skills / Ctrl+H** agora mostra a contagem e prévia das referências
  numéricas recebidas/citadas pela habilidade selecionada; continua somente
  um inspetor de dados, sem ativar habilidades.
- `cache/skill_trace.lua` inclui rótulos do APK e é **privado/local**.
  `reports/skill_trace_summary.json` contém apenas contagens, hashes,
  IDs exemplificativos e limitações, adequado para GitHub público.

Reproduza depois de extrair o APK e gerar a Fase 21:

```bash
python tools/catalogar_habilidades.py
python tools/rastrear_habilidades.py
python -m pytest -q tests
```

**Validação:** 74 testes + 10 subtestes passaram. Sem teste gráfico real no
Windows. A cena Ctrl+P com movimento e prévia de ataques está preservada,
sem causar dano a entidades e sem criar regras inventadas.

---

## Fase 21 — catálogo de habilidades e análise do ciclo de execução (ainda não há dano funcional)

A reconstrução continua sendo **fiel ao BarbarQ**, sem substituir mecânicas por outras inventadas. Nesta etapa:

- `tools/catalogar_habilidades.py` interpreta as tabelas `config.skill.*.txt` por campos de descrição com tamanho UTF-8 em **bytes**. Valida IDs únicos, comprimentos, referências e caracteres UTF-8 sem executar dados do APK.
- As oito tabelas auditadas contêm **31.119** configurações `heroskillconfig`, **566** vínculos `functionbindskill`, **687** registros `functiondamage`, **1.489** `functionanimation`, **726** `functionrandomskill`, **27.948** `functiondelayskill`, **84** `selectsector` e **98** `skilleventregister`.
- **566/566** vínculos de botão apontam para IDs existentes de habilidades. Por exemplo, o registro `10039` (ataque do bárbaro) indica código de botão `2` e habilidade `4010020` na configuração original. Isto **não comprova** equivalência com a tecla J, K ou L, que são atalhos de prévia.
- `tools/analisar_habilidades.py` audita **sete funções**, **494 instruções ARM64**, com checagem SHA-256 do ELF. `Hero::onButtonClicked` solicita uma habilidade e a entrega a `Entity::addSkill`. O construtor seleciona entre `CSelfSkill` e `CMultiTargetSkill` conforme o tipo `10050`. A função base `CSkill::Update(float)` contém apenas `ret`; subclasses podem possuir comportamentos próprios.
- Um painel **Habilidades** fica disponível por clique na aba superior ou **Ctrl+H**; lista vínculos e seus IDs usando o arquivo local `cache/skill_catalog.lua`. A interface permanece de **pesquisa**, não executa habilidades.
- Os relatórios públicos `reports/skill_catalog_summary.json` e `reports/native_skill_flow.json` contêm metadados e IDs, sem copiar recursos, tabelas completas ou código de máquina.

**Preparação do cache da Fase 21:** após extrair o APK e preparar as demais tabelas como nas etapas anteriores, execute `python tools/catalogar_habilidades.py`. O cache e os recursos permanecem locais, fora do GitHub.

**Validação:** `python -m pytest -q tests` passou com **71 testes e 10 subtestes**. Não foi executado teste gráfico no Windows. A física da cena de teste, a escolha da animação, o dano, o hitbox, a seleção de alvos e o cooldown **não estão comprovados como fiéis**.

---

## Fase 19 — objetos de mapa TMX com física experimental (NÃO partida original)

**Inventário verificado no APK 1.0.1811:** 32 arquivos `.tmx`; apenas os cinco
`petisland_01` a `petisland_05` possuem `objectgroup`. Cada um descreve um
retângulo no espaço do mapa em **(x=395, y=138, largura=232, altura=238)**.
As referências são dados Tiled: nenhum atributo do objeto o classifica como
parede, terreno sólido ou zona de dano. Os arquivos `.tsx` associados não contêm
colisores individuais de tiles. **Não afirmamos que estes sejam obstáculos do
jogo original.**

- `tools/preparar_recursos.py` preserva hierarquias de objetos, identificadores,
  nomes, formatos, coordenadas, visibilidade e propriedades declaradas no TMX.
- `src/map_objects.lua` separa retângulos válidos e verifica sobreposição
  em coordenadas da cena. Formas não retangulares não são convertidas em física.
- Em **Ctrl+P**, a tecla **O** alterna a sobreposição visual dos objetos TMX,
  sem modificar o mapa. **K** alterna um **teste físico opcional**, construído
  com fixtures Box2D: começa como sensor (não sólido) e só se torna sólido
  quando o bárbaro estiver fora do retângulo, evitando ativação dentro de um
  obstáculo. O modo de colisão é desativado ao reiniciar a cena.
- `C` continua controlando o debug físico existente. O retângulo laranja é
  o obstáculo **artificial** da Fase 18 e permanece identificado como tal.
- Validação: `python -m pytest -q tests` — 64 testes, 10 subtestes
  adicionais, sem falhas. Reprocessamos os 32 TMX com os recursos originais.

**Limites:** a forma de usar os cinco retângulos no motor nativo continua
indeterminada; o tratamento da colisão física no LÖVE2D é uma experiência de
isolamento. A cena não é uma partida jogável e não houve teste gráfico do
executável em Windows.

---

## Fase 18 — primeira cena controlável (laboratório físico, NÃO partida original)

A aba **Teste** (atalho **Ctrl+P**) acrescenta uma cena **controlável** em
**LÖVE2D 11.x com `love.physics` (Box2D)**, usando somente recursos visuais
recuperados do APK **1.0.1811**: a imagem do mapa `petisland_01` (`tilemaps/pvetiled.png`)
e a animação `character/babarian/babarian.bexportjson` com as texturas `babarian0`.
São exibidas poses `stand_0` e `walk_0` e variantes 1–5 dos movimentos
originais, avaliadas pelo mesmo renderizador experimental da F5.

**Como experimentar** (com `assets_original/` e `cache/` preparados):

1. Abra a pasta do projeto no LÖVE2D 11.x e pressione **Ctrl+P** (ou clique na aba **Teste**).
2. **WASD/setas** movem o bárbaro; **R** reinicia a cena; **1–5** selecionam
   uma variante visual da animação; **C** mostra ou oculta os contornos físicos;
   a roda do mouse ajusta o zoom; no painel à esquerda pode-se escolher outro
   mapa extraído do APK.
3. Um pequeno **retângulo laranja** é um **obstáculo de depuração artificial**,
   desenhado com contorno. **Não faz parte do mapa oficial**. Os limites da área
   são corpos estáticos de teste; **não recuperamos os obstáculos do terreno**.

**Fatos recuperados × hipóteses do teste**

| Elemento | Procedência |
|---|---|
| `petisland_01`, PNG dos tiles, sprite e movimentos `stand/walk` | **Original do APK**, em leitura local |
| `love.physics.newWorld` / corpo dinâmico / contato Box2D | **Implementação funcional** no LÖVE2D (motor Box2D) |
| `categoryBits=1, maskBits=3, groupIndex=0` | **Confirmado** antes na F17 para `Entity::setCollidable(true)` |
| Corpo circular de raio 18 px, velocidade-base `300/100` × 30 px/s | **Hipóteses de depuração**, não medidas do BarbarQ |
| Paredes de borda e retângulo de teste | **Artificiais**, não colisões reais do mapa |
| Interpolação do esqueleto e reprodução a 30 fps | **Aproximação experimental**, não garantia de equivalência 1:1 |

Um relógio de física com passo fixo **1/60 s**, delta limitado e normalização
WASD diagonal reduz variações dependentes da taxa de quadros. O código separa
criação do mundo, entrada, atualização e renderização no módulo
`src/playtest.lua`, com testes `tests/test_playtest.lua` (mock rigoroso das
chamadas físicas) e `tests/test_playtest_integration.lua` (animação/atlas/mapa
reais). A presença do módulo `love.physics` é verificada antes de iniciar.

**Auditoria:** `python -m pytest -q` — **60 testes e 10 subtestes aprovados**
no ambiente de análise. A renderização e os contatos físicos no Windows
**não foram validados num executável LÖVE2D real**, porque ele não estava
instalado neste ambiente. Não há combate, bots, lógica de rede, habilidades,
regras de dano, obstáculos oficiais nem partida jogável.

---

## Fase 17 — filtros de contato Box2D recuperados (NÃO jogável)

Analisamos estaticamente `Entity::setCollidable(bool)`,
`b2ContactFilter::ShouldCollide`, `b2Fixture::SetFilterData` e
`config::hero::CollisionConfig::load` na biblioteca ARM64 **do APK 1.0.1811**.
`tools/analisar_filtros.py` confere SHA-256, endereços, tamanhos e instruções;
os relatórios `reports/native_filters.json` e `.lua` contêm somente metadados.

- `Entity::setCollidable(true)` constrói um filtro com **categoryBits=1,
  maskBits=3, groupIndex=0** e invoca `SetFilterData` no fixture examinado.
- `Entity::setCollidable(false)` usa **categoryBits=0, maskBits=1, groupIndex=0**.
- `b2ContactFilter::ShouldCollide`: se ambos compartilham um `groupIndex` não
  nulo, retorna verdadeiro apenas para grupo positivo. Caso contrário exige
  **(A.maskBits & B.categoryBits) != 0** e **(B.maskBits & A.categoryBits) != 0**.
- `SetFilterData` atualiza os campos do fixture e marca proxies relevantes no
  broadphase; mudar um filtro não aplica força nem resolve colisões por si só.
- `CollisionConfig::load` recupera um tipo inteiro e referências opcionais a
  descrições de formas; ainda não identificamos filtros exclusivos por herói.
- **F13 — Filtros Box2D** reproduz somente essa decisão em Lua, com teclas
  **A/B** para alternar os filtros dos fixtures, **G** para alternar grupo
  0/+1/-1 e **R** para reiniciar. A matriz de referência inclui quatro pares.

Auditoria reproduzível com sua cópia local da biblioteca:

```powershell
py tools/analisar_filtros.py --so "lib/arm64-v8a/libcocos2dcpp.so" --manifest reports/native_arm64.json
py -m unittest discover -s tests -v
```

**Limitações:** a simulação de filtros não executa Box2D, não cria contatos nem
faz o herói andar. Resultados de `ShouldCollide` não garantem contato físico:
corpos precisam estar próximos e outras regras ainda se aplicam. Não inferimos
filtros dos demais fixtures a partir dos valores de `Entity::setCollidable`.
A execução gráfica real no Windows permanece sem validação.

## Fase 16 — inicialização de corpo físico e colisores (não jogável)

A análise estática do **APK 1.0.1811**, vinculada ao SHA-256 do `libcocos2dcpp.so`, verificou duas funções AArch64: `Entity::InitB2Body` (51 instruções) e `Entity::InitCollision` (246 instruções). A localização e o tamanho foram confrontados com `.dynsym`; os padrões de instruções são auditados antes da geração dos relatórios. **Não é uma implementação funcional do Box2D.**

- `InitB2Body` reutiliza o corpo se o ponteiro já existe; senão chama `b2World::CreateBody`. A coordenada inicial é dividida por **100.0** (valor de `float` lido do segmento ELF). Um argumento booleano pode acionar `b2Body::SetType`.
- `InitCollision` discrimina os códigos de configuração **1, 2 e 3**, associados nesta função à criação de **fixture circular**, **polígono de quatro vértices** e **forma personalizada (polígonos gerados por `CustomShapeUtils`)**, respectivamente. As rotinas observadas chamam `CreateFixture` e `SetFixedRotation`, sob condições internas.
- Os fatores `-0.005` e `+0.005` usados num ramo de polígono foram lidos diretamente dos segmentos ELF. Esses fatores não são necessariamente unidades universais do jogo.
- **F12** mostra as evidências por função. Não processa colisões reais, filtros Box2D, máscaras, entidades controláveis ou partidas.

Reproduza a investigação com a cópia local do APK previamente extraída:

```bash
python tools/analisar_colisores.py --so lib/arm64-v8a/libcocos2dcpp.so --manifest reports/native_arm64.json
python -m unittest discover -s tests -q
```

O GitHub publica somente código e os metadados da investigação; **não contém** os binários extraídos, sprites nem APK original. No pacote local completo, pressione **F12** para abrir o novo painel. A execução gráfica real em Windows com LÖVE2D ainda não foi testada.

## Fase 15 — cadeia de contatos do Box2D (investigação estática; NÃO jogável)

Analisados **8 métodos ARM64 e 457 instruções** da `libcocos2dcpp.so` fornecida com o APK 1.0.1811, com endereço, tamanho e SHA-256 obrigatoriamente conferidos. O analisador está em `tools/analisar_contatos.py` e produz `reports/native_contacts.json` e `reports/native_contacts.lua` **somente com metadados**, sem publicar código nativo.

- `b2World::Step(float,int,int)` contém chamadas a `b2ContactManager::FindNewContacts`, `Collide`, `Solve` e `SolveTOI` (nem todos os caminhos são executados sempre).
- `b2ContactManager::Collide` chama `b2Contact::Update`; este faz chamadas indiretas de listener, condicionadas ao estado do contato.
- O listener **específico do jogo** `wildsContactListener::BeginContact` verifica, por entidade, um indicador no offset `0x1c1`. Quando habilitado, encaminha um vetor do contato a `Entity::ProcessContact`. O listener analisa ambos os lados separadamente.
- `EndContact`, `PreSolve` e `PostSolve` da classe `wildsContactListener` estão compilados apenas como `ret` nesta versão.
- `Entity::ProcessContact(b2Vec2)` contém `cosDeg`, `sinDeg` e `atan2Deg`, e grava um campo inteiro de orientação. **Não é prova de cálculo de dano ou de resposta física completa.**
- **Nova aba F11 — Contatos ARM64:** selecionar funções e consultar os metadados de fluxo, sem simular colisões.

Executar novamente a auditoria a partir de sua própria cópia do APK:

```powershell
py tools/analisar_contatos.py --apk "caminho\para\barbarq.apk"
py -m unittest discover -s tests -v
```

**Limitações:** não foram reproduzidos integrador físico, filtros de colisão, geometria dos corpos, resolução de contatos, frequência de frames ou mensagens de rede. As chamadas listadas são evidências estáticas; não demonstram que foram executadas em uma partida. A execução gráfica no Windows ainda não foi testada.

## Fase 14 — Entity::move / Box2D (laboratório; NÃO jogável)

**Base verificável:** a auditoria estática de `Entity::move(float,float)` na biblioteca ARM64
`libcocos2dcpp.so` do APK BarbarQ **1.0.1811** confirmou **59 instruções e 21 padrões**,
com os endereços validados após conferir o SHA-256 do arquivo. A função foi localizada
na tabela de símbolos nativos em **0xE4A88C** (236 bytes). Relatórios disponíveis em
`reports/entity_move.json` e `.lua`; nenhum trecho do binário é redistribuído.

- **Caminho 1 (bit 5 das flags ativo):** se o tipo do corpo for zero, retorna;
  caso contrário armazena os componentes `x,y` diretamente no corpo físico (`+0x40`).
  Se há movimento não nulo e o bit 1 estava desativado, esse bit é ativado e o
  contador interno em `+0xAC` é zerado. O significado desses bits no comportamento
  final do jogo ainda precisa de confirmação.
- **Caminho 2 (bit 5 desativado):** para deslocamentos próximos de zero
  (limiar original `±0,0001`, armazenado como float32), retorna. Caso contrário
  calcula `posição_anterior + (dx/30, dy/30)` e chama `b2Body::SetTransform`
  preservando o ângulo previamente lido.
- **Nova aba F10:** `Entity / Box2D` exibe os resultados previstos pelo fluxo
  do ELF. **Setas** alteram `dx/dy`; `G` alterna bit 5, `T` alterna o tipo de
  corpo (zero/não-zero), `Z` zera componentes, `Enter` aplica **somente** a posição
  proposta na ferramenta, `R` reinicia. Essa ferramenta não executa Box2D.
- **Ferramenta:** `tools/analisar_entidade.py --apk caminho.apk --manifest
  reports/native_arm64.json --out reports` exige LLVM e Binutils, valida os símbolos,
  offsets e padrões observados, gera relatórios somente com metadados.

**Limites importantes:** `SetTransform` não é uma física completa: não foram
reconstruídos passo de simulação, colisões, contatos, IA, servidor, mecanismos de
previsão ou comandos em tempo real. Os cálculos Lua não reproduzem todos os detalhes
de arredondamento float32 do ARM64. Testes automatizados concluídos localmente, mas
**sem execução gráfica no Windows**. O projeto segue não jogável.

## Fase 13 — codificação de controle e vetores do ARM64 (laboratório, ainda não jogável)

**Base confirmada:** APK BarbarQ 1.0.1811 ARM64, `libcocos2dcpp.so` com SHA-256 conferido. O analisador `tools/analisar_movimento.py` verifica **23 padrões** de instruções em **cinco funções nativas**, extrai constantes `100.0`, `π` e `180.0` das regiões `PT_LOAD` e produz `reports/native_movement.json`/`.lua`. O relatório publica somente metadados, não a biblioteca nem os bytes do código.

- `Hero::setStickDir(int)` grava um inteiro no deslocamento `+0x324`; `Hero::setSpeed(int)` grava outro em `+0x328`. São offsets de memória da versão estudada, não um protocolo de rede público.
- `Hero::move_update(float)` usa campos `+0x328`, `+0xd8`, `+0xdc` para construir a soma de dois vetores com `cosDeg`/`sinDeg`; componentes de velocidade são divididos por 100. O resultado é passado a `Entity::move(float,float)`. **Ainda não sabemos** a taxa temporal, colisões, controle de terreno nem as demais regras de `Entity::move`.
- `GameScene::updateStick()` usa quatro inteiros em `+0x434`/`+0x438`/`+0x43c`/`+0x440`, valores 90/180/270 e um cálculo por média ponderada, além de um ramo que converte radianos em graus. Os campos não receberam nomes de teclas porque isso não foi comprovado.
- A direção é quantizada por grupos de aproximadamente 4 graus, com casos especiais `-1`, `0→89` e `180→44`; valores como `359` podem resultar em **90**, portanto não pressupomos intervalo 0–89.
- Quando o código de direção muda, o programa original monta uma mensagem `COperateMessage__ThumbnailMove` e chama `BattleNet::SendCmd`; `+0x2c` guarda o código de direção e `+0x28` uma sequência incrementada em 2. Isso **não comprova** que o transporte e a partida online sejam reproduzíveis.
- `src/movement_codec.lua` implementa a aritmética observada para inspeção. `src/movement_view.lua` adiciona **F9 — Movimento ARM64** com visualização interativa dos dois vetores e sua soma. Setas ajustam ângulo e velocidade; `J/K` ligam os vetores, `A/Z` alteram a segunda velocidade, `Q/E` o segundo ângulo e `R` reinicia.

**Limitações essenciais:** os cálculos em Lua usam números double, enquanto o executável opera com inteiros de 32 bits e floats ARM64; diferenças de arredondamento podem ocorrer. O laboratório F9 não controla um personagem nem envia comandos, e não foi executado graficamente no Windows. O port 1:1 e a jogabilidade continuam pendentes.

## Fase 12 — fluxo estático de funções ARM64 (não jogável)

A ferramenta **`tools/analisar_fluxo.py`** usa `llvm-objdump` para examinar **10 funções** com endereços e tamanhos identificados na Fase 11. Confere o SHA-256 da `libcocos2dcpp.so` antes de analisar e produz `reports/native_flow.json` e `reports/native_flow.lua`, contendo **somente metadados** (quantidade de instruções, chamadas diretas `BL`, indiretas `BLR`, desvios condicionais e nomes de alvos). Os relatórios não contêm bytes de executável nem instruções copiadas.

- **1.576 instruções** de 10 funções ARM64 verificadas nos endereços originais.
- `Hero::setStickDir(int)` contém apenas `str` seguido de `ret`, o que é evidência de armazenamento de um argumento numa posição da estrutura (não demonstra a escala ou regra do movimento).
- `GameScene::updateStick()` referencia a construção de `COperateMessage__ThumbnailMove` e `BattleNet::SendCmd` com esse tipo de mensagem, mostrando uma ligação entre controle e envio de operações.
- `GameScene::updateLogicFrame(float)` tem chamadas para `BattleManager`, `BattleNet`, `ReplaySystem` e `SpectatorSystem`. Um alvo estático **não comprova** que a chamada é executada em todas as partidas.
- `CSkill::Update(float)` nesta biblioteca específica contém **uma única instrução de retorno**; isso não significa que o sistema de habilidades inteiro seja vazio.
- **F8 Fluxo ARM64:** aba somente leitura para consultar os alvos estáticos e contadores por função; F1–F7 preservadas. Não executa instruções nativas.

Para reproduzir o relatório com a **mesma versão 1.0.1811** do APK (Windows: LLVM instalado no PATH ou WSL):

```powershell
py tools/analisar_fluxo.py --apk "C:\caminho\BarbarQ-1.0.1811.apk" --symbols reports/native_symbols.csv --manifest reports/native_arm64.json --out reports
py -m unittest discover -s tests -v
```

**Limitações:** a listagem identifica transferências de controle no código compilado, não é rastreamento dinâmico, não identifica destinos de chamadas indiretas por vtables, não reconstrói variáveis, protocolos completos, IA, colisões, fórmulas ou gameplay. Nenhuma funcionalidade jogável foi reivindicada. Não foi realizado teste gráfico real no Windows.

## Estado atual — Fase 11: símbolos do motor nativo ARM64

O projeto ainda é **um laboratório de visualização; não é uma versão jogável**.

### Investigação da biblioteca nativa (Fase 11)

- `tools/auditar_elf.py`: audita exclusivamente arquivos ELF64 AArch64 dentro do **APK local**. Usa `readelf` e `c++filt`, sem carregar ou executar bibliotecas. Valida cabeçalho, tamanho máximo e diretórios permitidos antes de analisar.
- `libcocos2dcpp.so` (aprox. 38,1 MiB) é marcado como *stripped*, mas preserva **83.660 entradas anunciadas** de `.dynsym` (83.658 entradas com nome interpretáveis pelo leitor), incluindo funções C++ nomeadas do jogo. Isso fornece pontos de partida para análise dirigida; não equivale à recuperação de código-fonte ou algoritmos.
- O relatório extrai e classifica **586 símbolos de métodos** em 12 classes de interesse (`GameScene`, `BattleNet`, `BattleManager`, `BattleFieldController`, `GameLayer`, `Hero`, `CSkill`, `CSkillEntity`, `CMoveEdge`, `ViewMoveEdge`, `BattleDataManager`, `UILayer`). Exemplos efetivamente presentes: `BattleNet::processFrameUpdate`, `GameScene::processPursueFrame`, `Hero::setStickDir`, `CSkill::Update`, `BattleManager::createEntity`.
- `reports/native_arm64.json`, `reports/native_symbols.csv` e `reports/native_findings.lua` contêm **apenas nomes de símbolos, endereços virtuais, contagens e hashes**, sem redistribuir bibliotecas nem outras partes do APK.
- **F7 — ELF ARM64:** mostra os nomes de classes, contagens e amostras de funções do relatório para navegação no LÖVE2D. É ferramenta de pesquisa, não uma mecânica jogável.
- A presença de nomes como `processFrameUpdate`, `setStickDir` e `CreateSkillBySkillConfigId` **não demonstra** qual algoritmo, frame rate, regra de sincronização ou fórmula de combate o BarbarQ usa. Isso exigirá análise de fluxo e testes com o cliente original.

Executar a auditoria numa máquina com Python 3.10+ e Binutils/LLVM (no Windows pode usar WSL):

```powershell
python tools/auditar_elf.py "C:\caminho\para\BarbarQ.apk" --out reports
python -m unittest discover -s tests -v
```

Os relatórios que acompanham esta versão foram gerados **do APK BarbarQ 1.0.1811 enviado pelo usuário**. Para outra versão, gere relatórios novamente; endereços não são portáveis entre versões.

- **Fase 10 — subcenas:** o CSB declara 1.005 nós `ProjectNode`; 985 apontam para cenas que estão presentes no próprio APK e 20 não contêm nome válido. A aba F6 permite selecionar um `ProjectNode` e pressionar `Enter` para inspecionar a cena referenciada, e `Backspace` para retornar. Há bloqueio de ciclos, caminhos inválidos, ambiguidades e profundidade acima de 16. Isto **não** corresponde à navegação real do jogador entre menus; são referências de composição de cena.
- **Fase 10 — botões:** recuperadas 2.313 imagens de estado normal, 612 de estado pressionado e 956 de estado desabilitado dos 2.909 botões encontrados. `H` alterna somente os estados declarados para o botão selecionado, como ferramenta de inspeção visual; não executa cliques ou callbacks do jogo. Quatro nós em toda a coleção apresentam callback textual `Click`, insuficiente para reconstruir a lógica.
- **Auditoria:** `cache/summary.json` registra contagens de cenas, referências, skins e callbacks. O parser original continua defensivo contra referências malformadas.

- **VISPACK:** extrator de arquivos do APK 1.0.1811 (ARM64).
- **Cenas Cocos Studio:** 560 arquivos `.csb` FlatBuffers decodificados, com 26.612 nós de interface recuperados, incluindo 6.820 `ImageView`, 6.099 `Text`, 5.449 `Panel` e 2.909 `Button`. Nomes, caminhos de imagem, `actionTag`, posições, escalas, âncoras, dimensões e hierarquia são convertidos para `cache/scenes.lua`.
- **Aba F6 aprimorada:** inspeção de hierarquia, geometria e imagens reais dos atlas/PNGs quando presentes. Regras de layout, fontes e ações do Cocos ainda não são reconstruídas integralmente.
- **Mapas:** lê 32 mapas TMX base64/zlib e suas texturas; a câmera e o retículo são apenas ferramentas de investigação.
- **Atlas:** lê 171 `.bplist` FlatBuffers e 2 `.plist` XML; **13.875 recortes de sprites** catalogados. Uma textura referenciada não está presente no APK.
- **Animações:** lê os **1.079 `.bexportjson` binários (FlatBuffers)** e reconstrói os metadados de **1.079 armaduras, 2.657 movimentos, 7.452 trilhas de ossos e 38.727 keyframes**.
- **F5 atualizado:** leitura da pose-base, interpolação linear de keyframes, matrizes afins e composição de parentesco **somente quando informado nos dados**.
- **Troca real de imagens:** `bone[2]` fornece o display inicial; `frame[0]` seleciona o display por keyframe (índice baseado em zero, com `-1` = invisível). Os índices de **2.552 ossos** e **38.727 quadros-chave** foram conferidos contra suas próprias listas de displays: nenhum índice fora dos limites. Uma posição vazia é mantida no vetor para não deslocar índices posteriores.
- **Ordem de renderização:** `bone[5]` contém a ordem numérica de camada observada (em 1.022/1.079 armaduras, sequência contínua de 1 a N); renderização estável de trás para frente, mantendo a ordem original quando há empate. Sua semântica ainda depende de comparação visual com o motor original.
- **Busca de sprites melhorada:** dá prioridade aos atlas `.plist` declarados na própria animação (mapeando-os aos `.bplist` existentes), depois ao diretório da animação; somente usa nomes globais quando a associação é inequívoca.
- **Comparação A/B:** teclas `I` (interpolação ligada/desligada) e `B` (pose-base ligada/desligada) para inspecionar hipóteses de transformação sem confundir a prévia com o motor Cocos.
- **Correção do leitor:** a antiga hipótese de usar `frame[11]` como `display_index` continua descartada. A Fase 6 confirma o verdadeiro índice em `frame[0]` e usa `bone[2]` como display inicial.
- **F1/F2/F3/F4:** painéis de mapa, imagens, atlas e configurações preservados.

### Fase 8: reconstrução dos metadados de interfaces

- O leitor `tools/csb.py` decodifica o contêiner `CSParseBinary` e a árvore `NodeTree` de 560 cenas sem executar nenhum arquivo binário como código. A estrutura dos campos usa como referência o esquema público do Cocos Studio, **não** a lógica proprietária do jogo.
- Recuperados **26.612 nós** com verificação de limites, contagens máximas, validade UTF-8, profundidade da árvore e transformações finitas. Recurso e texto são extraídos apenas de tipos identificados.
- `tools/preparar_recursos.py` gera `cache/scenes.lua` e atualiza `summary.json` com número de cenas, nós e classes.
- A aba **F6** apresenta um retângulo de layout por componente, sua hierarquia, origem, tamanho e `z` declarados. Tenta exibir uma textura original **somente** quando ela existe como arquivo avulso no APK. A busca compara caminhos sem diferenciar maiúsculas/minúsculas, como no Android.
- Inspeção disponível por `Tab`/`Shift+Tab` (nó seguinte/anterior), `G` (guias) e `V` (exibir nós ocultos).
- **Limitações:** a geometria é uma projeção de depuração. Não implementa escalonamento responsivo do Cocos, `scale9`, fontes customizadas, sprites de atlas, clipping de painéis, rotação completa, blend, fluxo de eventos ou ações de botões. Um botão exibido em F6 **não funciona** como um botão de jogo. O cache local não deve ser publicado no GitHub público por conter dados originais.

### Fase 7: geometria dos sprites corrigida

- **Orientação das imagens:** cada textura recortada agora é desenhada com a inversão vertical correta entre o atlas (+Y para baixo) e as coordenadas locais Cocos (+Y para cima). A implementação antiga podia apresentar sprites invertidos.
- **Alinhamento do trim:** `offset_x`/`offset_y`, `source_w`/`source_h` e dimensões reais do recorte são considerados de forma uniforme em F3 e F5. O recorte não é esticado artificialmente para o tamanho original.
- **Referência visual F3:** quadro amarelo indica a área da imagem original; quadro verde indica os limites da parte visível do sprite. A origem usada é o centro do quadro original (âncora 0,5 × 0,5, uma **hipótese explícita**).
- **Depuração F5:** a tecla `P` alterna as guias amarelas (imagem original), verdes (recorte) e cruz vermelha (origem do osso). As guias acompanham a transformação local e a pose do osso.
- **Interpolação subquadro:** F5 passa o tempo fracionário ao avaliador de poses; anteriormente arredondava antes da interpolação, ocultando as transições.
- **Quadros rotacionados:** o módulo Lua tem um caminho condicional de desrotação para futuros recursos `rotated=true`, mas a auditoria desta versão do APK identificou **0/13.875 sprites rotacionados**. A convenção de rotação é **não validada** com dados reais deste jogo; não reivindicamos uma correção de recurso que não existe no material atual.
- **Auditoria de atlas:** 13.875 sprites dos 173 atlas; 9.181 têm dimensões recortadas, 9.108 apresentam offsets, e os recortes permanecem dentro dos retângulos de origem declarados.

**Limites da prévia F7:** os cálculos de pose-base + deltas e a decomposição de skew são **hipóteses de reconstrução**. A interpolação atual é linear e não replica easing Cocos; os assets analisados não expuseram nenhum `parent` textual não vazio para os ossos, então composição de pais está implementada e testada artificialmente, **mas não validada num esqueleto real do APK**. Ainda faltam: cor/blending, prova dos pivôs/âncoras de displays, easing, temporização original e reconciliação com captura do BarbarQ original. Não foram encontrados dados de ancoragem explícita nos displays comuns desta versão; a origem no centro é uma hipótese de visualização. A prioridade atual de atlas, a inversão vertical e a ordem das camadas precisam ser confrontadas visualmente com o jogo para confirmar o resultado. São usados 30 quadros/s **apenas para investigação**. Não apresentar o resultado como fiel 1:1 até comparação real.

**Não implementados:** controles de jogador, colisões, combate, IA, itens, menus operacionais, progressão, lobby e partidas online/offline. Ainda será necessária investigação do executável nativo e testes comparativos para uma portabilidade 1:1.

## Fase 9 — Atlas e componentes reais das cenas

- **Resolução de recursos:** `src/scene_resources.lua` mapeia caminhos virtuais dos arquivos `.csb` aos sprites dos atlas `.bplist` (`Gui/gui/Ver_6/...` → `gui/gui.bplist`) e texturas avulsas. Busca exata sem distinção entre maiúsculas/minúsculas e rejeição de nomes ambíguos; nenhuma substituição aleatória.
- **Auditoria:** nas 11.933 referências de imagens dos 560 arquivos `.csb`, há 10.868 referências apontam para nomes presentes nos atlas (10.866 resolvidas sem ambiguidades), 524 imagens avulsas e 541 referências não resolvidas. São ocorrências de referência (não imagens únicas); parte das ausências são placeholders do Cocos.
- **Transformação visual:** `src/scene_layout.lua` compõe âncora, posição, escala, flip, aproximação de `skew`/rotação e ordem z estável entre irmãos; permite selecionar um nó por posição usando matrizes inversas.
- **Aba F6:** desenha subtexturas com tamanho original e deslocamentos dos recortes, respeita opacidade herdada, oferece picking por clique e anotações textuais de depuração alternáveis (`T`). Menus ainda não são jogáveis; clicar seleciona componentes para inspeção, não aciona botões do BarbarQ.
- **Limitações:** layout responsivo, widgets `scale9`, fonts e eventos originais, ações, blending e renderização Cocos completa não estão implementados. As propriedades de `skew` são aproximadas e exigem comparação com capturas reais. Nenhum teste gráfico no Windows foi executado neste ambiente.

## Validação da Fase 10

Executado `python -m unittest discover -s tests -v`: **22 testes, sem falhas; 5 testes de integração antigos ficaram opcionais/skipped** por esperarem outro layout de diretórios. O novo teste audita os 560 CSBs reais, suas referências e os estados dos botões. `luatex --luaonly` cobre a navegação, ciclos, ida/volta e troca de skins. Cache regenerado e arquivos ZIP verificados. O teste gráfico real do LÖVE2D no Windows **ainda precisa ser feito**.

A maior parte da lógica de clique e de navegação do BarbarQ não está codificada nos CSB. Não há garantia de que um `ProjectNode` seja uma tela acessível por botão; ele pode representar apenas um fragmento visual reutilizado. A versão 1:1 exigirá engenharia reversa da biblioteca nativa original, validação de eventos e comparação em execução.

## Rodar o visualizador no Windows

Requisitos: [LÖVE2D 11.x](https://love2d.org/) e Python 3.10+.

```powershell
py tools/extrair_barbarq.py "C:\caminho\para\BarbarQ-1.0.1811.apk" --out assets_original
py tools/preparar_recursos.py --assets assets_original --out cache
& "C:\Program Files\LOVE\love.exe" .
```

Os ZIPs de teste **com recursos** já incluem `assets_original/` e `cache/`, então basta abrir a pasta com LÖVE2D. O ZIP **só com código** exige a extração a partir do APK local.

### Navegação

| Atalho | Operação |
|---|---|
| `F1` a `F8` | Mapas, imagens, atlas, configurações, animações, cenas CSB, símbolos nativos e fluxo ARM64 |
| `↑` / `↓` e clique | Selecionar um arquivo na lista lateral (F2–F5) |
| Digitar / `Esc` | Filtrar ou limpar a lista (F2–F5) |
| `WASD` e roda do mouse | Câmara e zoom na inspeção de mapas |
| `[` / `]` | Trocar sprite na aba de atlas F3 |
| `Espaço` | Pausar/continuar prévia F5 |
| `←` / `→` | Voltar/avançar um quadro F5 (pausa automaticamente) |
| `Tab` / `Shift+Tab` | Trocar de movimento F5 |
| `I` | Alternar interpolação linear e quadros discretos F5 |
| `B` | Alternar inclusão da pose-base F5 |
| `P` | Exibir/ocultar caixas do recorte, canvas original e origem F5 |
| `Tab` / `Shift+Tab` | Navegar entre nós da cena F6 |
| `G` / `V` | Alternar guias / nós ocultos na cena F6 |
| `T` / clique na cena | Mostrar/ocultar textos de referência / selecionar nó da cena F6 |
| `Enter` em ProjectNode | Abrir a cena `.csb` referenciada, somente para inspeção |
| `Backspace` em subcena | Retornar à cena anterior sem perder o nó selecionado |
| `H` em botão | Alternar entre imagens de estados declarados no CSB |

## Estrutura

| Diretório/arquivo | Papel |
|---|---|
| `tools/extrair_barbarq.py` | Extrai recursos do VISPACK |
| `tools/bplist.py` | Decodifica atlas `.bplist` com validação de limites |
| `tools/bexport.py` | Decodifica animações `.bexportjson` sem executar dados externos |
| `tools/csb.py` | Leitor FlatBuffers das cenas do Cocos Studio, com limites e validações |
| `src/scene_view.lua` | Visualizador F6 de hierarquias, recortes e seleção |
| `src/scene_resources.lua` | Resolver de recursos das cenas para atlas ou PNGs avulsos |
| `src/scene_layout.lua` | Matrizes de hierarquia 2D, ordem z e picking |
| `tools/auditar_elf.py` | Auditoria estática dos ELF AArch64, nomes de símbolos, hashes e endereços virtuais |
| `tools/analisar_fluxo.py` | Desmontagem estática dirigida a funções da Fase 11; publica somente os metadados de fluxo |
| `src/flow_view.lua` | Painel F8 somente leitura de referências de fluxo ARM64 |
| `src/native_view.lua` | Painel F7 com metadados de funções C++ exportadas; não executa código Android |
| `src/scene_links.lua` | Resolução exata de referências ProjectNode com proteção contra caminhos ambíguos |
| `tools/preparar_recursos.py` | Converte mapas, atlas e animações para cache Lua local |
| `src/animation_view.lua` | Visualizador F5 de poses, seleção de displays e sobreposição |
| `src/sprite_resolver.lua` | Resolução contextual de nomes de sprites e prevenção de colisões |
| `src/pose.lua` | Interpolação e matrizes afins, sem dependência gráfica |
| `src/sprite_geometry.lua` | Cálculo de recortes, origem, offsets e conversão de eixo, com suporte experimental para atlas rotacionados |
| `tests/test_sprite_geometry.lua`, `tests/test_animation_view.lua` | Testes Lua do posicionamento, orientação e integração da prévia |
| `tests/test_pose.lua` | Testes Lua de poses, transições discretas de display e ordem de camadas |
| `tests/test_sprite_resolver.lua` | Teste Lua de atlas explícitos, locais, globais e colisões |
| `main.lua`, `conf.lua` | Interface LÖVE2D |
| `tests/` | Testes Python; casos malformados e integração opcional |
| `assets_original/` | Recursos locais do APK; **ignorado pelo Git** |
| `cache/` | Dados locais gerados; **ignorado pelo Git** |

## Auditoria da Fase 7

```powershell
py -m unittest discover -s tests -v
py tools/preparar_recursos.py --assets assets_original --out cache
```

Os **15 testes Python passaram**, incluindo as suítes Lua de pose, resolução de sprites, geometria e desenho da aba F5 com Lua via `luatex --luaonly`. Os **1.079 arquivos binários foram novamente decodificados sem falhas**, inclusive todas as 38.727 poses-chave. Há 18 keyframes que ocultam a imagem com display `-1`. O cache local completo foi regenerado a partir do APK. Sintaxe Lua dos módulos conferida. **Ainda não houve teste visual no LÖVE2D/Windows neste ambiente**; nenhuma fidelidade visual está certificada.

## Próximas frentes

1. Executar a Fase 7 no LÖVE2D para Windows e comparar imagens e ordem de camadas com capturas do BarbarQ original; investigar âncoras, curvas de easing, cor e taxa de reprodução sem pressupor semântica não confirmada.
2. Decodificar cenas `.csb`, modelos `.c3b` e informações de configuração pertinentes à jogabilidade.
3. Reconstruir a movimentação, entidades, física e combate com testes de referência 1:1.
4. Investigar e, se viável, substituir serviços de rede por uma infraestrutura independente.

Este repositório público distribui somente o código-fonte da investigação. **Não publica** o APK, texturas, áudio, modelos ou outros recursos protegidos do jogo. Use sua própria cópia autorizada do APK para extrair os arquivos localmente.

### Referência de formato para CSB

O mapeamento dos campos comuns `.csb` foi confrontado com o projeto público [csb-flatbuffers-schema](https://github.com/halx99/csb-flatbuffers-schema) e com os arquivos fornecidos do APK. O leitor é uma implementação independente: não inclui nem redistribui o esquema ou binários de terceiros.

## Fase 20 — prévia dos três ataques do bárbaro (SEM combate)

- A auditoria `tools/analisar_ataques.py` verifica o SHA-256 da biblioteca nativa original e confirma 35 instruções em `Hero::onButtonClicked` e `Hero::getButtonState`.
- O primeiro método valida um índice de botão, verifica sua configuração e encaminha a criação da habilidade para `CSkill::CreateSkillBySkillConfigId` e `Entity::addSkill`. O segundo consulta um estado por índice. **Nenhuma correspondência entre os botões e `attack1/2/3` foi demonstrada.**
- O arquivo original `character/babarian/babarian.bexportjson` possui 15 movimentos `attack1/2/3` com 5 variantes cada; seus nomes e durações em quadros são registrados em `reports/native_attacks.json`.
- A cena de teste Ctrl+P agora usa as teclas **J/K/L para pré-visualizar** as três sequências originais, sem hitbox, dano, IA, efeitos, consumo, rede nem cooldown. Pressionar outra tecla de ataque antes de acabar a animação não a substitui; para reiniciar use R.
- **G** ativa/desativa a colisão TMX EXPERIMENTAL (era K na Fase 19); O mostra os objetos, C mostra colisores, WASD move.
- O conversor de quadros usa **30 fps apenas como convenção visual de investigação**, não é uma confirmação da taxa original de reprodução; não afirmar equivalência 1:1.
- Rode `python tools/analisar_ataques.py` e `python -m unittest discover -s tests -p 'test_*.py'` a partir da raiz para verificar a versão.
- Os binários e os assets do APK não pertencem ao repositório público.

## Fase 23 — fluxo ARM64 da busca de alvos e aplicação de dano (ainda sem combate)

- `tools/analisar_combate.py` confere o SHA-256 de `libcocos2dcpp.so` (APK 1.0.1811), os símbolos, tamanhos, endereços e as chamadas das **8 funções** escolhidas. Gera `reports/native_combat.json` e `reports/native_combat.lua`, apenas com metadados auditáveis, sem código proprietário.
- `CDamageFunction::Run()` encaminha para `Run(CSkillEntity*)` em um ramo; este pode invocar `GetDamageValue(bool*)` e `Hero::addHurtFromEnemy(...)`.
- `GetDamageValue(bool*)` consulta `GetParamValue(...)` e um gerador de números aleatórios. Isso **não revela** nem justifica uma fórmula de dano simplificada.
- `CSelectTargetSector::GetSelectTargets()` consulta direção e trigonometria e chama `b2World::QueryAABB`. **AABB é busca preliminar**, não prova da regra final de alvos atingidos.
- `CMultiTargetSkill::Update(float)` contém vínculo de função com entidade, e `Entity::skill_update(float)` chama `CSkill::Release()` em caminhos de limpeza.
- Nova aba **Combate ARM64** (`Ctrl+D`) para inspecionar os metadados no LÖVE2D. As 15 abas anteriores continuam disponíveis.
- **Limitações:** nenhuma animação J/K/L foi ligada com certeza ao cálculo de dano; não implementa alvos, hitbox, acerto, dano, cooldown ou combate. O visualizador para Windows continua precisando de verificação visual em ambiente LÖVE2D real.

Regerar o relatório usando sua própria extração: `python tools/analisar_combate.py --library lib/arm64-v8a/libcocos2dcpp.so`.
Os binários Android e recursos originais não devem ser enviados ao GitHub público.


## Fase 24 — núcleo matemático de `CDamageFunction::GetDamageValue` (não jogável)

A Fase 24 aprofunda a desmontagem do **mesmo APK 1.0.1811**, verificando o SHA-256 de `libcocos2dcpp.so`, os símbolos C++ e **29 operações específicas** entre as **332 instruções** de `GetDamageValue(bool*)`. Também confirma o valor `100.0` do objeto global `LogicWorkshopMgr::DECIMAL_RATIO`, conferindo sua relocação.

A expressão de um ramo da função é reproduzida apenas como **núcleo aritmético parcial**:

`base = A - B * (1 - C / 100)`

`fator = (sorteio <= trunc(limiar)) ? D / 100 : 1`

`parcial = base * fator * (1 - E / 100)`

Os seis parâmetros aparecem na configuração nativa nas posições `0x38`, `0x40`, `0x48`, `0x58`, `0x50`, `0x60` (na ordem A, B, limiar, C, D, E). A biblioteca também chama uma função de números aleatórios com argumentos observados `0, 1, 100`, **sem que sua distribuição seja assumida**. A função contém um retorno do valor previamente calculado, tratamento especial para tipo de mapa 7 e ajustes adicionais por entidade-alvo: esses ramos **não são emulados**.

- **Novo analisador:** `python tools/analisar_formula_dano.py` gera `reports/damage_math.json` e `reports/damage_math.lua` sem copiar instruções binárias para o GitHub.
- **Módulo isolado:** `src/damage_math.lua` reproduz exclusivamente os operadores aritméticos confirmados, recebendo parâmetros e sorteio explícitos; não gera sorteios, não altera HP e não executa efeitos.
- **Nova aba:** **Dano** (`Ctrl+M`) exibe proveniência, constantes e resultado de um exemplo **inventado somente para teste dos operadores**. As setas mudam o sorteio e o limiar desse exemplo, sem qualquer efeito no teste jogável.
- **Testes:** `python -m unittest discover -s tests -p 'test_*.py'` valida o binário original, o resultado Lua e as regressões existentes.

**Limites obrigatórios:** os valores concretos do bárbaro e da habilidade `4010020` não foram estabelecidos, nem o vínculo dessa habilidade ao cálculo, os modificadores de alvo, distribuição do RNG, arredondamento ou timing de acertos. A cena `Ctrl+P` continua **sem dano, inimigos ou combate funcional**. A execução gráfica real em Windows ainda está pendente de teste.


## Fase 25 — transição de HP e resolução de valores (pesquisa isolada)

`tools/analisar_valores_vida.py` valida por **SHA-256**, tabela ELF e instruções ARM64 os métodos `Entity::getValueByType` (duas variantes) e `Hero::addHurtFromEnemy(int,int,bool)` do APK BarbarQ 1.0.1811. Foram verificadas **3 funções, 269 instruções e 44 checkpoints**. O analisador gera `reports/entity_damage_flow.json` e `reports/entity_damage_flow.lua` sem carregar a biblioteca no jogo.

- O campo de HP atual fica no deslocamento `+0x314` de `Hero`. Quando HP é positivo, a rotina subtrai dano; se o novo HP for positivo, grava o resultado. Se chegar a zero ou menos, grava **zero** e o identificador da origem do golpe em `+0x370`, chama uma **rotina virtual** (resolvida na Fase 26 como `Entity::onDied`) e limita o dano contabilizado ao HP anterior.
- Há atualizações **condicionais** de estatísticas de dano recebido e infligido, dependentes de gerenciadores de dados e da presença da entidade atacante; também há emissão de evento e possível interrupção de combo. Os eventos, a rotina virtual e as estatísticas **não foram reimplementados**.
- `getValueByType` usa a razão percentual previamente confirmada na Fase 24. O ramo contextual reconhece identificadores especiais `1002` e `1003`; as variantes possuem um seletor de operação com casos `0` a `3` para adição, subtração, multiplicação e divisão, ignorando divisão quando o divisor é zero. As condições de quais entidades/atributos alimentar essas operações ainda exigem investigação.
- **Módulo de pesquisa:** `src/hero_hurt.lua` implementa apenas o ramo aritmético observado para **HP inteiro positivo** e **dano inteiro não negativo**. Os efeitos colaterais nativos e casos fora desse domínio são expressamente recusados. A aba **Vida** (`Ctrl+V`) permite testar HP e dano **fictícios**, sem aplicar qualquer dano na cena controlável.
- Os títulos das 18 abas foram abreviados para que o seletor superior fique legível em 1280px. O restante das abas e a cena Ctrl+P foram preservados.

**Reprodução:** `python tools/analisar_valores_vida.py` (necessita da biblioteca original local), seguido de `python -m unittest discover -s tests -q`. O pacote de código não inclui DLLs, SOs Android nem recursos proprietários. A ligação da habilidade `4010020` à fórmula de dano e o agendamento da rotina separada `dieLogic` e seus efeitos completos continuam não confirmados. Nenhum ataque causa dano real; a interface gráfica Windows/LÖVE ainda carece de validação manual.

## Fase 27 — encadeamento de morte e retorno do herói (pesquisa isolada)

A Fase 27 analisa **Hero::update(float), Hero::reborn(bool), Entity::reborn(bool) e Hero::resetReviveData(bool)** na biblioteca ARM64 do APK BarbarQ **1.0.1811**. O analisador `tools/analisar_renascimento.py` confere SHA-256, símbolos C++ exatos, endereços/tamanhos, relocações da vtable e checkpoints de desmontagem. Relatórios: `reports/reborn_flow.json` e `reports/reborn_flow.lua`.

**Ciclo de morte agora comprovado:** `Hero::addHurtFromEnemy` aciona virtualmente `Entity::onDied` quando a vida é zerada. `onDied` ativa o byte em `+0x1bc`. Mais tarde, em `Hero::update`, a leitura de `+0x1bc` encaminha ao slot virtual `+0x98`, que resolve para **Hero::dieLogic**. Isso corrige a lacuna sobre quem aciona o processamento de morte depois de `onDied`.

**Renascimento:** outro trecho de `Hero::update` testa um marco armazenado em `+0x574`, um indicador do `BattleManager` e uma diferença de contadores com limiar bruto `0x41a` (decimal **1050**). Se as condições observadas passam, a chamada virtual do slot `+0x50` alcança `Hero::reborn(true)`; esta chama `Entity::reborn`, reinicia dados, invoca `Hero::resetReviveData(bool)`, recupera habilidades extras condicionalmente e marca o jogador como vivo quando o registro existe. `resetReviveData` só consulta o lugar de nascimento aleatório e chama `b2Body::SetTransform` quando o parâmetro booleano é verdadeiro, além de executar rotinas de reinicialização, eventos, nível e pontuação.

**Atenção:** `1050` é um **limiar numérico do contador nativo**, não 1050 milissegundos, quadros ou segundos. Não foi confirmado o significado físico da unidade, a origem exata do marco, as regras completas dos modos ou o tempo de respawn percebido pelo jogador. O simulador Lua `src/reborn_rules.lua` apenas compara valores sintéticos sem overflow ou wraparound. Quando o marco vale `-1`, considera o caminho desativado, e nunca executa callbacks, timers reais, dano, física ou renascimento. O painel `src/reborn_view.lua` pode ser aberto com **Ctrl+B**. Os 19 painéis anteriores, inclusive Ctrl+P, continuam disponíveis.

Para reproduzir: use a sua própria extração `lib/arm64-v8a/libcocos2dcpp.so` e execute `python tools/analisar_renascimento.py`, seguido de `python -m unittest discover -s tests -q`. Não distribua o ELF e os assets originais no GitHub público. A execução gráfica real em Windows/LÖVE2D **continua sem validação manual**; a prévia Ctrl+P permanece experimental e não contém combate real ou respawn funcional.

## Fase 28 — `Hero::reInit` e diferenças de configuração (pesquisa isolada)

A análise estática do **BarbarQ 1.0.1811 ARM64** confirmou as funções `Hero::reInit(int,bool)`, `Hero::InitSkillAndAttri(...)` e `Hero::PlayerRestartGame()`: **447 instruções e 46 verificações de desmontagem**. `tools/analisar_reinit.py` confere SHA-256, símbolos ELF, endereços, tamanhos e instruções, exportando `reports/reinit_flow.json` e `reports/reinit_flow.lua`.

`Hero::reInit` calcula dois IDs de configuração `baseId + (level - 1) * 10000`, com nível novo e nível anterior armazenado em `Hero+0x180`. Se `full=true`, a função reconstrói parte do herói chamando `Hero::init` e `ReimportWithBringData`; **esse caminho não foi portado**. Se `full=false`, chama `Entity::setLevel` e ajusta campos com `valorAtual + (configNova - configAnterior)`.

Os campos de destino identificados pelo offset são `0xc0`, `0x32c`, `0x330`, `0x310`, `0x314`, `0x328`, `0x318`, `0x31c` e `0x1b8`. Correspondem, respectivamente, aos offsets da configuração `0x38`, `0x3c`, `0x40`, `0x44`, `0x44`, `0x48`, `0x4c`, `0x4c` e `0x50`. O campo `Hero+0xe0` recebe diretamente o valor da configuração `+0x48`. **Isso NÃO autoriza rotular individualmente todos esses campos como HP, ataque, defesa ou velocidade.** Os novos valores são operações `int32` no binário; o modelo Lua recusa overflow em vez de reproduzir silenciosamente wraparound.

Há ramos opcionais observados em `Hero+0x204` e no ponteiro da configuração `+0x88`. Eles estão fora de `src/reinit_rules.lua`; `applySimpleDelta` **exige** que o chamador declare explicitamente ambos inativos. A criação de habilidades compara listas de IDs extraídas do campo `+0x58`; o helper `newSkillIds` apenas exemplifica a diferença de listas, não chama `CSkill::CreateSkillBySkillConfigId` nem `Entity::addSkill`. O texto de configuração e os efeitos completos desses caminhos continuam sem equivalência Lua.

`Hero::InitSkillAndAttri` zera vários acumuladores e inicializa flags, antes de encaminhar para a implementação em `Entity`. `Hero::PlayerRestartGame` é **diferente de `Hero::reborn`**: zera o campo `+0x190`, redefine a origem do dano em `+0x370`, copia um marco do `BattleManager` para `+0x574` e emite um evento. Nem o novo módulo nem a aba F28 executam esse fluxo.

**Interface:** nova aba **ReInit**, com atalho `Ctrl+I`; as setas modificam um **exemplo fictício** de nível e delta e `R` restaura o exemplo. A cena experimental `Ctrl+P` e as vinte abas anteriores são preservadas. **Nenhum atributo do herói jogável é alterado pelo demonstrador.**

**Reprodução:** usando sua própria extração original `lib/arm64-v8a/libcocos2dcpp.so`, execute `python tools/analisar_reinit.py` e `python -m unittest discover -s tests -p 'test_*.py' -q`. Para verificação de sintaxe Lua, use `luatex --luaonly`. O binário Android e os recursos originais são mantidos fora do GitHub público. A execução real do aplicativo LÖVE2D no Windows ainda não foi testada, e o combate, as regras definitivas de nivelamento e o renascimento jogável permanecem incompletos.

## Fase 29 — Catálogo de progressão de atributos do APK (inspeção, não combate)

A auditoria cruza duas fontes da versão **1.0.1811**: as tabelas
`config.hero.heroconfig.txt` e `config.hero.entityconfig.txt` e os
opcodes ARM64 em `Hero::init`, `Hero::reInit` e `Hero::getValueByType`.

- **1.239** registros de HeroConfig e **2.734** registros de EntityConfig
  foram lidos, com prefixos de comprimento UTF-8 validados.
- **435** configurações iniciais distintas possuem correspondência direta
  em HeroConfig. Destas, **27** apresentam uma sequência de mais de um nível
  com o mesmo nome, totalizando **832** registros de nível nesses grupos.
  As outras referências de entidade **não são necessariamente corrompidas**:
  podem apontar para outras classes, variantes ou convenções de ID.
- O personagem bárbaro (`EntityConfig 210000`, base `HeroConfig 210001`)
  tem os IDs `210001`, `220001`, `230001` nos três primeiros níveis.
  A primeira posição numérica candidata à posição `HeroConfig +0x38`
  assume os valores brutos **195**, **200** e **205**.
- `Hero::init` carrega os campos `HeroConfig +0x38..+0x54`, e o caminho
  incremental de `Hero::reInit` aplica diferenças de configurações aos
  campos internos correspondentes. `Hero::getValueByType` consulta diversos
  campos para retornar valores do herói. O auditor **verifica as instruções,
  endereços e símbolos** desses três métodos (696 instruções ARM64,
  34 checkpoints), além do SHA-256 do ELF original.

**Limite da identificação:** a associação entre a ordem dos números
no arquivo `.txt` e os offsets do `HeroConfig` é **posicional**, ainda não
confirmada por um esquema serializado da configuração. A semântica de cada
campo (`HP`, ataque, defesa, velocidade etc.) **não foi demonstrada**.
Não mudar o jogo ou o cálculo de dano com essas colunas sem cruzamento
adicional no código nativo.

### Novos arquivos e uso

- `tools/catalogar_niveis.py`: gera `cache/hero_levels.lua` a partir de
  recursos locais originais (cache privado, não publicado no GitHub) e
  `reports/hero_level_catalog.json` com números, IDs de exemplo e hashes.
- `tools/analisar_atributos.py`: verifica os três métodos nativos e gera
  `reports/hero_attr_arm64.json` e `.lua`, sem anexar o executável ao ZIP.
- `src/level_attributes.lua`: consulta e calcula diferenças **sem alterar**
  o personagem, sua vida ou seus atributos reais.
- `src/level_attributes_view.lua`: aba **Níveis** acessível por `Ctrl+L`.
  Escolha um personagem na lista lateral; use **←/→** para mudar o nível
  e **R** para reiniciar a seleção. A lista só aparece se o cache local for
  gerado. A aba anterior `ReInit` continua acessível por `Ctrl+I`.

Testes novos: `test_catalogar_niveis.py`, `test_analisar_atributos.py`,
`test_levels_runner.py` e `test_level_attributes.lua`. Testes Python/Lua
verificam o bárbaro e entradas inválidas; a verificação nativa exige o ELF
original, ausente na distribuição pública. LÖVE2D Windows ainda não foi
executado para validação gráfica.

**Objetivo seguinte:** investigar o esquema `config::hero::HeroConfig` ou
seus getters para atribuir nomes aos slots com evidências, e só então
integrar progressão real ao personagem controlável.

## Fase 30 — Esquema de `HeroConfig`, HP e `ValueType` (com evidência ARM64)

A investigação percorre `config::hero::HeroConfig::load`, `Hero::init`,
`Hero::addHurtFromEnemy` e `Hero::getValueByType` na versão **BarbarQ
1.0.1811 ARM64**. O novo `tools/analisar_esquema_heroi.py` confere o
**SHA-256** da biblioteca e da tabela `config.hero.heroconfig.txt`, quatro
símbolos ELF completos, instruções nos endereços exatos e os 32 destinos
de salto da tabela do dispatch. São **586 instruções auditadas**.

**Nova evidência:** `HeroConfig::load` decodifica oito inteiros consecutivos
pelos offsets **`+0x38, +0x3c, +0x40, +0x44, +0x48, +0x4c, +0x50, +0x54`**.
A ordem confirma a associação posicional à tabela de configuração usada na
Fase 29. `Hero::init` copia o valor do offset **`HeroConfig+0x44`**
para **`Hero+0x314` (HP atual)** e **`Hero+0x310` (referência inicial de HP)**.
`Hero::addHurtFromEnemy` lê/escreve `Hero+0x314`, confirmando sua função.
`Hero::getValueByType` usa **código numérico 5** para ler `Hero+0x314`
e **código 11** para ler `Hero+0x310`. Não afirmar que `+0x310`
é necessariamente um máximo imutável em todos os estados do jogo.

Nos três primeiros níveis da configuração do bárbaro (`210001`, `220001`,
`230001`), o HP inicial bruto recuperado é **240, 240, 240**. O campo `+0x38`
continua representando **195, 200 e 205**, mas **não deve ser rotulado HP**:
são slots diferentes. Os outros sete campos inteiros permanecem sem rótulo
semântico confirmado (ataque, defesa, velocidade etc.). Os demais códigos
de `ValueType` são registrados pelo offset real ou pelo tipo de caminho,
mas sem nomes de atributos conjecturais.

Arquivos novos ou alterados:

- `tools/analisar_esquema_heroi.py`: auditoria de hashes, símbolos, opcodes e
tabela de despacho; exporta `reports/hero_schema.json` e `.lua`.
- `src/hero_schema.lua`: consulta apenas valores confirmados e valida
`ValueType=5`/`11`, sem tocar nos atributos do personagem.
- `src/level_attributes_view.lua`: a aba **Níveis (Ctrl+L)** marca somente
`0x44` como HP inicial. **T** alterna entre níveis e os 32 códigos de
`ValueType`; **←/→** navegam e **R** reinicia.
- `tests/test_hero_schema_runner.py` e `tests/test_hero_schema.lua`:
validação contra ELF/tabelas originais, detecção de hash falso,
comportamento Lua e integração da interface.

Para reproduzir, extraia legalmente seus próprios recursos do APK 1.0.1811,
depois execute `python tools/analisar_esquema_heroi.py` e
`python -m unittest discover -s tests -p 'test_hero_schema_runner.py' -v`.
O APK, o `.so` e os recursos extraídos **não são publicados no GitHub**.
A cena Ctrl+P continua experimental, sem dano, morte ou renascimento
funcional, e não houve validação gráfica manual no Windows/LÖVE2D.


## Fase 31 — Velocidade-base confirmada em `HeroConfig`

Esta etapa acrescenta um segundo atributo semanticamente comprovado pelo
executável ARM64 original, sem modificar o playtest ou converter resultados
em uma velocidade de tela não validada.

- `HeroConfig+0x48` alimenta `Hero+0x328` em `Hero::init`; o mesmo valor é
  copiado para `Hero+0xe0`, cuja semântica permanece em estudo.
- `Hero::setSpeed(int)` grava `Hero+0x328`, confirmando o campo de
  **velocidade-base**.
- `Hero::move_update(float)` lê esse campo quando o respectivo estado interno
  permite e o divide por **100** antes de calcular a componente de movimento.
  O movimento também usa `Hero+0xd8`, `Hero+0xdc`, direção e estados internos.
- `Hero::getValueByType` expõe o valor por **ValueType 19**; HP atual e
  referência continuam correspondendo aos códigos 5 e 11.
- O valor do campo `0x48` do bárbaro no nível 1 é **150**. Após o divisor
  resulta em componente **1,5**, sem implicar pixels por segundo ou
  velocidade total; a escala e a temporização ainda não foram reconstruídas.

A cadeia é auditável em `tools/analisar_semantica_heroi.py`, com conferência
de SHA-256, símbolos, 648 instruções ARM64 (incluindo as 586 já verificadas na
Fase 30), *checkpoints* de opcodes e o divisor extraído da seção PT_LOAD.
O relatório público está em `reports/hero_semantics.json` e
`reports/hero_semantics.lua`. O catálogo privado extraído do APK continua
fora do repositório.

A aba **Níveis** (`Ctrl+L`) indica agora `0x44: HP inicial` e
`0x48: velocidade-base`. Pressione **T** nessa aba para ver os códigos
ValueType. Os seis outros campos permanecem anônimos, e **nenhum atributo é
aplicado à cena controlável**.

**Limites:** não há correspondência confiável de `0x38`, `0x3c`, `0x40`,
`0x4c`, `0x50` e `0x54` com ataque, defesa e outras estatísticas. O
visualizador continua experimental e não houve validação gráfica em um
Windows real.

**Validação F31:** 142 testes Python/Lua aprovados em 4 grupos; foi excluída uma auditoria antiga integral de 560 cenas CSB por duração excessiva. 100 arquivos Lua passaram na verificação sintática. A interface gráfica ainda não foi validada em Windows com LÖVE2D.
