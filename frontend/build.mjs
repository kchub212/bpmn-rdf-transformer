import * as esbuild from 'esbuild'

await esbuild.build({
  entryPoints: ['src/bpmn-entry.js', 'src/turtle-entry.js'],
  bundle: true,
  outdir: '../src/bpmn_rdf_transformer/api/static/vendor',
  format: 'iife',
  minify: false,
})

console.log('Build complete.')
