const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const css = fs.readFileSync(path.join(__dirname, '..', 'styles.css'), 'utf8');
const library = require('../friend-characters.js');
const root = path.resolve(__dirname, '..');
const ids = ['pikachu','bulbasaur','iron-man','spider-man','harry-potter','hermione','bloop','sprout','pip','roo','mira','orbit','paws'];

test('all six supplied images use bundled original-scene assets, not transparent cutouts', () => {
  for (const c of library.characters.slice(0, 6)) {
    const full = path.join(root, c.src);
    assert.ok(fs.existsSync(full), `${c.id} original scene file is missing`);
    assert.ok(fs.statSync(full).size > 10000, `${c.id} source scene is unexpectedly small`);
    assert.match(c.src, /character-scenes\/.+scene\.png$/);
  }
});

test('all thirteen characters have their own square scene stage palettes', () => {
  for (const id of ids) {
    assert.match(css, new RegExp(`data-character-id=["']${id}["'][^}]*\{[^}]*--char-bg-a`, 's'), `${id} is missing its themed stage palette`);
  }
});

test('same square dimensions are used on desktop and mobile', () => {
  assert.match(css, /\.friend-character-choice-art[\s\S]*?width:\s*104px[\s\S]*?height:\s*104px/);
  assert.match(css, /@media\s*\(max-width:\s*760px\)[\s\S]*?\.friend-character-choice-art[\s\S]*?width:\s*92px[\s\S]*?height:\s*92px/);
});

test('whole uploaded scenes remain visible using contain-fit rather than background-removing crop', () => {
  assert.match(css, /\.friend-character-choice-art img[\s\S]*?object-fit:\s*contain/);
  assert.match(css, /--character-scene-image/);
  assert.match(css, /background-image:[\s\S]*?var\(--character-scene-image/);
  assert.match(css, /cpFullSceneCamera/);
  assert.match(css, /cpFullSceneBackdrop/);
  assert.match(css, /cpFullSceneLightSweep/);
});

test('all thirteen characters have distinct full-scene animation rhythms', () => {
  for (const id of ids) assert.ok(css.includes(`data-character-id="${id}"`), `${id} is missing an animation selector`);
  for (const name of ['Pikachu','Bulbasaur','IronMan','Spider','Harry','Hermione','Bloop','Sprout','Pip','Roo','Mira','Orbit','Paws']) {
    assert.match(css, new RegExp(`@keyframes cpScene${name}`));
  }
});
