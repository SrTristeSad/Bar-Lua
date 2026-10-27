-- Carrega sintaxe sem iniciar o aplicativo/gráfico (LÖVE não disponível nesta máquina).
assert(loadfile('main.lua'))
assert(loadfile('src/movement_codec.lua'))
assert(loadfile('src/movement_view.lua'))
assert(loadfile('reports/native_movement.lua'))
print('F13 Lua syntax OK')