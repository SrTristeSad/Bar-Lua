for _,f in ipairs({'main.lua','src/contact_filter.lua','src/filter_view.lua','reports/native_filters.lua'}) do
  local chunk,err=loadfile(f)
  assert(chunk,f..': '..tostring(err))
end
print('F17 syntax OK')
