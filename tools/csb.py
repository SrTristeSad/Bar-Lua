"""Leitor defensivo de cenas Cocos Studio CSB/FlatBuffers do APK BarbarQ.

Decodifica somente campos com semântica corroborada pelo layout público do
CSParseBinary e por inspeção do APK. Não executa scripts do jogo ou dados.
Suporta o subconjunto de WidgetOptions, ResourceData e nós de UI. Não é um
renderizador Cocos Studio nem converte física, lógica, animações ou callbacks.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import math
import struct
from bplist import Buffer, BPlistError

class SceneError(ValueError):
    pass

MAX_FILE = 12 * 1024 * 1024
MAX_NODES = 12000
MAX_DEPTH = 70
MAX_VECTOR = 15000
MAX_TEXT = 2048

class Reader(Buffer):
    def f2(self, addr):
        if addr is None: return None
        x, y = self.get('<f', addr), self.get('<f', addr + 4)
        if not all(math.isfinite(v) and abs(v) <= 1e7 for v in (x,y)):
            raise SceneError('Coordenada 2D inválida')
        return [round(x, 4), round(y, 4)]

    def u8(self, at):
        return self.get('<B', at)

    def vector(self, field, kind):
        if field is None: return []
        target = self.deref(field)
        count = self.uint(target)
        if count > MAX_VECTOR or target+4+count*4 > self.size:
            raise SceneError('Vetor FlatBuffers inválido')
        result = []
        for i in range(count):
            slot = target + 4 + i*4
            if kind == 'string': result.append(self.string(slot))
            elif kind == 'table': result.append(self.table(self.deref(slot)))
            else: raise SceneError('Tipo de vetor desconhecido')
        return result


def _str(t, field):
    text=t.string(field)
    if len(text)>MAX_TEXT:raise SceneError('Texto excessivo')
    return text


def _int(t, field, default=0):
    p=t.addr(field)
    return t.r.int(p) if p is not None else default


def _u8(t, field, default=0):
    p=t.addr(field)
    return t.r.u8(p) if p is not None else default


def _point(t, field):
    return t.r.f2(t.addr(field))


def _resource(t):
    if not t:return None
    name=_str(t,0); plist=_str(t,1)
    typ=_int(t,2)
    if name and len(name)>500:raise SceneError('Caminho longo')
    if not name and not plist:return None
    return {'path':name, 'plist':plist, 'type':typ}


def _widget(t):
    if t is None:return {}
    data={'name':_str(t,0), 'tag':_int(t,6), 'action_tag':_int(t,1),
          'z':_int(t,3), 'visible':_u8(t,4,1)!=0,
          'opacity':_u8(t,5,255), 'position':_point(t,7) or [0,0],
          'scale':_point(t,8) or [1,1],
          'anchor':_point(t,9) or [0.5,0.5],
          'size':_point(t,11) or [0,0],
          'skew':_point(t,2) or [0,0],
          'flip_x':bool(_u8(t,12)), 'flip_y':bool(_u8(t,13)),
          'touch':bool(_u8(t,15)), 'callback':_str(t,18)}
    col=t.addr(10)
    if col is not None:
        data['color']=[t.r.u8(col+i) for i in range(4)]
    return data


def _node(tree, reader, counters, depth):
    if depth>MAX_DEPTH:raise SceneError('Profundidade da cena excessiva')
    counters['nodes']+=1
    if counters['nodes']>MAX_NODES:raise SceneError('Cena com nós demais')
    kind=_str(tree,0)
    if not kind or len(kind)>150:raise SceneError('Classe inválida')
    counters[kind]+=1
    options=tree.nested(2)
    specialized=options.nested(0) if options else None
    widget=(specialized if kind=='Node' else specialized.nested(0)) if specialized else None
    data={'class':kind, 'props':_widget(widget)}
    custom=_str(tree,3)
    if custom:data['custom_class']=custom
    # Sprite/ImageView/Panel/Button/etc: campo 1 da opção costuma ser ResourceData,
    # mas em algumas classes (ProjectNode) é uma string; não reinterpretamos.
    if specialized and kind in {'Sprite','ImageView','Panel','Button','LoadingBar','CheckBox','ScrollView','PageView','ListView','Slider','Particle','ParticleSystem','GameMap'}:
        d=specialized.nested(1)
        if d:
            res=_resource(d)
            if res:data['resource']=res
    if specialized and kind in {'Text','TextField','Button','TextBMFont'}:
        index={'Text':4,'TextField':4,'Button':5,'TextBMFont':2}[kind]
        label=_str(specialized,index)
        if label:data['text']=label[:MAX_TEXT]
    children=reader.vector(tree.addr(1),'table')
    data['children']=[_node(ch, reader, counters, depth+1) for ch in children]
    return data


def parse_bytes(data:bytes)->dict:
    if len(data)<20 or len(data)>MAX_FILE:
        raise SceneError('Tamanho CSB inválido')
    try:
        reader=Reader(data)
        root=reader.table(reader.uint(0))
        version=_str(root,0)
        if not version or len(version)>40:
            raise SceneError('Versão CSB ausente')
        top=root.nested(3)
        if top is None:raise SceneError('Árvore principal ausente')
        counters=Counter()
        node=_node(top,reader,counters,0)
        return {'version':version, 'textures':reader.vector(root.addr(1),'string'),
                'texture_pngs':reader.vector(root.addr(2),'string'),
                'root':node,'node_count':counters['nodes'],
                'classes':{k:v for k,v in counters.items() if k!='nodes'}}
    except (BPlistError,struct.error,OverflowError,UnicodeError) as exc:
        raise SceneError(str(exc)) from exc


def parse_file(path:Path)->dict:
    return parse_bytes(Path(path).read_bytes())