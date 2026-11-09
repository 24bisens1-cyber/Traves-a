const test = require('node:test');
const assert = require('node:assert/strict');
const library = require('../friend-characters.js');

test('friend library prioritizes supplied character art and retains the original TRAVESÍA companions', () => {
  const ids = library.characters.map((item) => item.id);
  assert.deepEqual(ids.slice(0, 6), ['pikachu', 'bulbasaur', 'iron-man', 'spider-man', 'harry-potter', 'hermione']);
  for (const id of ['bloop', 'sprout', 'pip', 'roo', 'mira', 'orbit', 'paws']) assert.ok(ids.includes(id), `missing ${id}`);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(!ids.includes('traveller'), 'the old generic City explorer avatar is no longer a choice');
  for (const character of library.characters.slice(0, 6)) assert.match(character.src, /assets\/character-scenes\/.+scene\.png$/, `${character.id} must use its full-scene image`);
});

test('twelve friends receive twelve different defaults, starting with the supplied images', () => {
  const people = Array.from({ length: 12 }, (_, index) => `Friend ${index + 1}`);
  const selected = library.normalize(people, {});
  assert.equal(Object.keys(selected).length, 12);
  assert.equal(new Set(Object.values(selected)).size, 12);
  assert.deepEqual(people.slice(0, 6).map((person) => selected[person]), ['pikachu', 'bulbasaur', 'iron-man', 'spider-man', 'harry-potter', 'hermione']);
  assert.deepEqual(people.slice(6).map((person) => selected[person]), ['bloop', 'sprout', 'pip', 'roo', 'mira', 'orbit']);
});

test('the six uploaded original-background scenes are the first six defaults', () => {
  const supplied = library.characters.slice(0, 6);
  assert.deepEqual(supplied.map((item) => item.src.split('/').pop()), ['pikachu-scene.png', 'bulbasaur-scene.png', 'iron-man-scene.png', 'spider-man-scene.png', 'harry-potter-scene.png', 'hermione-scene.png']);
});

test('legacy generic traveller selections are migrated to distinct supplied/default characters', () => {
  const people = ['Friend 1', 'Friend 2', 'Friend 3', 'Friend 4'];
  const selected = library.normalize(people, Object.fromEntries(people.map((person) => [person, 'traveller'])));
  assert.deepEqual(people.map((person) => selected[person]), ['pikachu', 'bulbasaur', 'iron-man', 'spider-man']);
});

test('existing valid choices persist when loading a saved trip', () => {
  const people = ['A', 'B', 'C'];
  const selected = library.normalize(people, { A: 'hermione', B: 'iron-man', C: 'sprout' });
  assert.deepEqual(selected, { A: 'hermione', B: 'iron-man', C: 'sprout' });
});

test('duplicate saved selections are repaired deterministically', () => {
  const people = ['A', 'B', 'C', 'D'];
  const selected = library.normalize(people, { A: 'pikachu', B: 'pikachu', C: 'iron-man', D: 'iron-man' });
  assert.equal(selected.A, 'pikachu');
  assert.notEqual(selected.B, 'pikachu');
  assert.equal(selected.C, 'iron-man');
  assert.notEqual(selected.D, 'iron-man');
  assert.equal(new Set(Object.values(selected)).size, people.length);
});

test('available options hide characters assigned to other friends', () => {
  const people = ['A', 'B', 'C'];
  const selected = { A: 'pikachu', B: 'sprout', C: 'hermione' };
  const available = library.available(people, selected, 'B').map((item) => item.id);
  assert.ok(available.includes('sprout'));
  assert.ok(!available.includes('pikachu'));
  assert.ok(!available.includes('hermione'));
});

test('assign allows a friend to change to an unused character', () => {
  const people = ['A', 'B'];
  const selected = { A: 'pikachu', B: 'sprout' };
  const updated = library.assign(people, selected, 'B', 'hermione');
  assert.equal(updated.B, 'hermione');
  assert.equal(updated.A, 'pikachu');
});

test('assign refuses a character that another friend already has', () => {
  const people = ['A', 'B'];
  const selected = { A: 'pikachu', B: 'sprout' };
  assert.throws(() => library.assign(people, selected, 'B', 'pikachu'), /already assigned to A/);
});
