# Bar-Lua — BarbarQ 1.0.1811 (portabilidade Windows)

**Objetivo:** estudar o APK original e reconstruir fielmente o BarbarQ em **Lua/LÖVE2D**, nativo para Windows, sem usar emulador Android. **Não é um jogo inspirado**: qualquer sistema adicionado deve ser baseado no original ou identificado explicitamente como instrumento de pesquisa.

## Situação atual (fase 2 — pesquisa visual e mapas)

- Extrator do pacote **VISPACK** presente no APK `com.bbqstudio.bbqqoversea`, versão **1.0.1811**.
- Leitor offline dos mapas originais `.tmx` (base64/zlib; tilesets embutidos e externos `.tsx`).
- Conversor de atlas XML `.plist` para tabelas Lua, com identificação de **195 frames** em dois atlas XML; `.bplist` e animações binárias ainda não decodificados.
- Visualizador LÖVE2D com painéis **F1 Mapas**, **F2 Imagens**, **F3 Atlas**, **F4 Configurações**, carregando os recursos extraídos do APK.
- Renderização dos tiles realmente presentes no mapa (com limitação da área visível), câmera WASD, zoom e troca de mapa.
- Nenhum APK, textura, som, modelo ou outro recurso protegido é distribuído neste repositório público.

**Ainda NÃO é jogável.** O retículo amarelo é um marcador de depuração da câmera, **não** um personagem do jogo. Combate, colisões, habilidades, personagens animados e multiplayer aguardam análise do código nativo e validação. As flags de inversão/rotação do Tiled ainda não são renderizadas; o GID é apresentado em orientação normal. A área de atlas mostra a imagem original, não as animações reconstruídas.

## Como abrir no Windows

Requisitos: **Python 3.10+** e **[LÖVE2D 11.x](https://love2d.org/)**.

1. Clone/baixe este repositório.
2. Coloque o **seu APK original** em uma pasta local (fora do GitHub).
3. Abra PowerShell na pasta do repositório e execute:

```powershell
py tools/extrair_barbarq.py "C:\caminho\para\BarbarQ-1.0.1811.apk" --out assets_original
py tools/preparar_recursos.py --assets assets_original --out cache
& "C:\Program Files\LOVE\love.exe" .
```

Se desejar somente os recursos dos mapas, imagens, atlas e tabelas para pesquisar:

```powershell
py tools/extrair_barbarq.py "C:\caminho\BarbarQ-1.0.1811.apk" --out assets_original --ext tmx,tsx,png,jpg,jpeg,plist,txt
py tools/preparar_recursos.py
```

Teclas: **F1–F4** alteram o painel, setas ou clique escolhem arquivos, digitar filtra; **Esc** limpa filtro, **roda do mouse** altera zoom, **WASD** move a câmera no mapa. A visualização de mapas foi pensada para investigação e não deve ser confundida com uma partida.

## Arquitetura

| Caminho | Uso |
|---|---|
| `tools/extrair_barbarq.py` | Desempacotamento VISPACK da versão 1.0.1811 |
| `tools/preparar_recursos.py` | Converte TMX/TSX e atlas plist XML em tabelas Lua locais |
| `main.lua`, `conf.lua` | Interface e renderizador de pesquisa LÖVE2D |
| `tests/` | Validação Python contra dados locais do APK |
| `assets_original/` | **Gerada pelo usuário, ignorada pelo Git** |
| `cache/` | **Gerada pelo preparador, ignorada pelo Git** |

## Plano de reconstrução 1:1

1. **Recursos:** atlas binário `.bplist`, animações `.bexportjson`, modelos `.c3b`, áudio FMOD e formatos de cenas.
2. **Regras:** estudar `configdata/`, código nativo (`libcocos2dcpp.so`) e comportamento observável para inferir entidades, controle, combates e progressão. Registrar lacunas sem preencher com invenções.
3. **Jogo local:** portar motor 2D/3D aplicável, física, habilidades e cenas reais; testes comparativos por versão.
4. **Conectividade:** avaliar dependências dos serviços antigos e alternativas próprias, sem alegar compatibilidade online sem provas.

### Limitações importantes

A extração bem-sucedida do conteúdo de um APK **não** equivale à recuperação do código-fonte. Nomes, dados e imagens são pistas, não evidência de que a regra ou o mapa está completo ou ativo na versão analisada. **Arquivos originais e demais direitos continuam pertencendo a seus titulares**; a extração deve ser feita localmente a partir do seu APK, sem publicá-los neste repositório.