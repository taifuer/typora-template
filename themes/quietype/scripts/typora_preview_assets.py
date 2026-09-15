"""Read installed Typora renderers into ignored build output for local previews."""
import json
from pathlib import Path
import re
import struct


def prepare_runtime(resources, output):
    output.mkdir(parents=True, exist_ok=True)
    # These files are read from the local installation, never shipped in the ZIP.
    with (resources / 'lib.asar').open('rb') as archive:
        header = struct.unpack('<4I', archive.read(16))
        tree = json.loads(archive.read(header[3]))
        offset = 8 + header[1]

        def extract(node, prefix=''):
            for name, item in node.get('files', {}).items():
                relative = prefix + name
                if 'files' in item:
                    extract(item, relative + '/')
                elif relative in ('diagram/mermaid.min.js', 'codemirror/mode.min.js') or relative.startswith('MathJax3/'):
                    target = output / relative
                    if not target.resolve().is_relative_to(output.resolve()):
                        raise ValueError('Invalid archive path')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    archive.seek(offset + int(item['offset']))
                    target.write_bytes(archive.read(item['size']))

        extract(tree)

    # Typora bundles its modified CodeMirror as a self-contained SystemJS module.
    # Isolate that module only, without starting the application's document logic.
    source = (resources / 'appsrc/window/frame.js').read_text(encoding='utf-8')
    version = re.search(r'\.version="5\.\d+\.\d+"', source)
    if not version:
        raise RuntimeError('Cannot locate the installed CodeMirror 5 renderer')
    start = source.rfind('$__System.registerDynamic(', 0, version.start())
    end = source.find(',$__System.registerDynamic(', version.end())
    module = source[start:end]
    if start < 0 or end < 0 or not re.match(r'\$__System.registerDynamic\("[^"]+",\[\],', module):
        raise RuntimeError('Unsupported Typora CodeMirror bundle; update the preview extractor')
    overlay_pos = source.index('.overlayMode=function')
    overlay_start = source.rfind('$__System.registerDynamic(', 0, overlay_pos)
    overlay_end = source.find(',$__System.registerDynamic(', overlay_pos)
    if overlay_start < 0 or overlay_end < 0:
        raise RuntimeError('Cannot locate the installed CodeMirror overlay addon')
    shim = ('window.File.option={passiveEvents:true};window.File.editor={sourceView:{inSourceMode:false}};\n'
        'var $__System={registerDynamic:function(id,deps,flag,fn){var m={exports:{}};fn(function(){return window.CodeMirror},null,m);if(typeof m.exports==="function")window.CodeMirror=m.exports;}};\n'
        'window.require=function(name){if(name==="codemirror/lib/codemirror.js"||name==="codemirror")return window.CodeMirror;throw Error("Unsupported preview dependency: "+name)};\n')
    (output / 'codemirror/core.js').write_text(shim + module + ';\n' + source[overlay_start:overlay_end] + ';\n', encoding='utf-8')
    return output
