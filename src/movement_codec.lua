-- F13: tradução de operações aritméticas OBSERVADAS no ARM64 do APK 1.0.1811.
-- Não substitui Entity::move: física/colisão/rede permanecem não reconstruídas.
local M = {}

local function integer(n)
    assert(type(n) == 'number' and n == n and n ~= math.huge and n ~= -math.huge, 'número finito exigido')
    assert(n % 1 == 0 and n >= -2147483648 and n <= 2147483647, 'int32 exigido')
    return n
end

local function finite(n)
    assert(type(n) == 'number' and n == n and n ~= math.huge and n ~= -math.huge, 'número finito exigido')
    return n
end

function M.quantize_degrees(angle)
    local v = integer(angle)
    if v == -1 then return -1 end
    if v == 0 then return 89 end
    if v == 180 then return 44 end
    if v < 0 then return math.floor(v / 4) end
    return math.floor((v + 3) / 4)
end

function M.radians_to_degrees_int(radians)
    local angle = math.modf(finite(radians) / math.pi * 180)
    if angle < 0 then angle = angle + 360 end
    return integer(angle)
end

function M.scene_direction(a, b, c, d, touching, angle_radians)
    a, b, c, d = integer(a), integer(b), integer(c), integer(d)
    if a ~= c or b ~= d then
        local sum = a + b + c + d
        assert(sum ~= 0, 'divisão por zero: estado inconsistente')
        local direction = (a == 0 or d == 0) and 315 or math.modf((90 * b + 180 * c + 270 * d) / sum)
        return M.quantize_degrees(direction), direction
    end
    if touching then return -1, -1 end
    local degrees = M.radians_to_degrees_int(angle_radians)
    return M.quantize_degrees(degrees), degrees
end

function M.changed_direction(previous, next_dir)
    next_dir = integer(next_dir)
    if previous == next_dir then return false, previous end
    return true, next_dir
end

function M.move_vector(speed, secondary_speed, facing_degrees, direction_degrees,
                       primary_enabled, secondary_enabled)
    speed, secondary_speed = integer(speed), integer(secondary_speed)
    facing_degrees, direction_degrees = integer(facing_degrees), integer(direction_degrees)
    local primary = primary_enabled and speed / 100 or 0
    local secondary = secondary_enabled and secondary_speed / 100 or 0
    local rad = math.pi / 180
    return secondary * math.cos(facing_degrees * rad) + primary * math.cos(direction_degrees * rad),
           secondary * math.sin(facing_degrees * rad) + primary * math.sin(direction_degrees * rad)
end

function M.message_fields(sequence, direction)
    sequence, direction = integer(sequence), integer(direction)
    return {sequence = sequence + 2, direction = direction, visual_degrees = direction * 4}
end

return M
