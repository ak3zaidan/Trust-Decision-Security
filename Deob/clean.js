const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generator = require('@babel/generator').default;
const t = require('@babel/types');

const code = fs.readFileSync('vm411b.js', 'utf8');

const ast = parser.parse(code, {
  sourceType: 'unambiguous',
  plugins: ['jsx']
});

// Generate pretty code
const output = generator(ast, {
  retainLines: false,
  compact: false,
  concise: false,
  quotes: 'single',
}).code;

// Save the result
fs.writeFileSync('pretty_output.js', output);

console.log('Deobfuscation complete. See pretty_output.js');
