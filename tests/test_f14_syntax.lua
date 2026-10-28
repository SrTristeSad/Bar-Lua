local names={'main.lua','src/entity_move.lua','src/entity_move_view.lua','reports/entity_move.lua'}
for _,file in ipairs(names) do
    local fn,err=loadfile(file)
    assert(fn, file..': '..tostring(err))
end
print('F14 syntax OK')
