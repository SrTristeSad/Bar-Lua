"""Playable arena tests; graphical LÖVE execution remains a separate smoke test."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ArenaGameplayTests(unittest.TestCase):
    def test_source_wired_as_default_mode(self):
        main=(ROOT/"main.lua").read_text(encoding="utf8")
        self.assertIn('local arenaGame = require("src.arena_game")',main)
        self.assertIn('local arenaView = require("src.arena_view")',main)
        self.assertIn('gameplayActive = true',main)
        self.assertIn('arenaState = arenaGame.new(originalArt.bounds(arenaVisuals))',main)
        self.assertIn('arenaVisuals = originalArt.prepare(maps,animations,atlases)',main)
        self.assertIn('arenaView.draw(arenaState',main)
        self.assertIn('originalArt.drawHero', (ROOT/"src/arena_view.lua").read_text(encoding="utf8"))
        self.assertIn('key == "space" or key == "j"',main)
    def test_arena_logic_lua(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua","luatex") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        cmd=[exe]+(["--luaonly"] if Path(exe).name=="luatex" else [])+["tests/test_arena_game.lua"]
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("ARENA GAMEPLAY LUA OK",result.stdout)
    def test_actor_collision_and_ai(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        result=subprocess.run([exe,"tests/test_arena_collision.lua"],cwd=ROOT,
                              capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("ARENA COLLISION AND AI LUA OK",result.stdout)
    def test_enemy_catalog_lua(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        result=subprocess.run([exe,"tests/test_arena_enemy_catalog.lua"],cwd=ROOT,
                              capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("ARENA ENEMY CATALOG LUA OK",result.stdout)
    def test_original_art_module_lua(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        result=subprocess.run([exe,"tests/test_arena_original_art.lua"],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("ORIGINAL ARENA ART LUA OK",result.stdout)
    def test_love_affine_transform(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        result=subprocess.run([exe,"tests/test_love_affine.lua"],cwd=ROOT,
                              capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("LOVE AFFINE LUA OK",result.stdout)
    def test_syntax_of_love_modules(self):
        exe=next((shutil.which(x) for x in ("lua5.4","lua","luajit","texlua") if shutil.which(x)),None)
        if not exe:self.skipTest("Lua interpreter unavailable")
        for target in ("main.lua","src/arena_game.lua","src/arena_view.lua","src/arena_original_art.lua","src/arena_enemy_catalog.lua","src/arena_collision.lua","src/love_affine.lua","src/playtest.lua"):
            code="assert(loadfile("+repr(target)+"))"
            result=subprocess.run([exe,"-e",code],cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,target+"\n"+result.stderr)

if __name__=="__main__":unittest.main()
