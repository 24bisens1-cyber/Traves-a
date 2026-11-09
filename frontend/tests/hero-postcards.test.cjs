const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const appSource = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');
const helperMatch = appSource.match(/function getHeroPostcardAlternatives\(scenes, selectedName\)\s*\{[\s\S]*?\n\}/);
assert.ok(helperMatch, 'the homepage must define a reusable postcard alternative selector');
const getAlternatives = vm.runInNewContext(`${helperMatch[0]}; getHeroPostcardAlternatives;`);
const scenes = [
  { name: 'Goa, India', image: 'goa.webp' },
  { name: 'Kyoto, Japan', image: 'kyoto.webp' },
  { name: 'Antarctica', image: 'antarctica.webp' },
];

test('Goa is active: floating postcards offer Kyoto and Antarctica', () => {
  assert.deepEqual(Array.from(getAlternatives(scenes, 'Goa, India'), x => x.name), ['Kyoto, Japan', 'Antarctica']);
});

test('Kyoto is active: Goa returns as a clickable alternate beside Antarctica', () => {
  assert.deepEqual(Array.from(getAlternatives(scenes, 'Kyoto, Japan'), x => x.name), ['Goa, India', 'Antarctica']);
});

test('Antarctica is active: Goa returns as a clickable alternate beside Kyoto', () => {
  assert.deepEqual(Array.from(getAlternatives(scenes, 'Antarctica'), x => x.name), ['Goa, India', 'Kyoto, Japan']);
});

test('the selected postcard is never duplicated among the two floating cards', () => {
  for (const scene of scenes) {
    const alternatives = getAlternatives(scenes, scene.name);
    assert.equal(alternatives.length, 2);
    assert.ok(alternatives.every(item => item.name !== scene.name));
  }
});

test('the rendered floating cards replace their destination, image, alt text and caption', () => {
  assert.match(appSource, /button\.dataset\.postcardDest=target\.name/);
  assert.match(appSource, /postcardImage\.src=target\.image/);
  assert.match(appSource, /postcardImage\.alt=target\.alt/);
  assert.match(appSource, /\$\{target\.name\} · VIEW THIS SCENE/);
  assert.match(appSource, /chooseHeroDestination\(postcard\.dataset\.postcardDest\)/);
});
