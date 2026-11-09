(function attachCityPulseFriendCharacters(root) {
  "use strict";

  const characters = Object.freeze([
    // Full uploaded scenes are preserved. The UI animates the complete image frame,
    // not a transparent character cutout or a cropped portrait.
    { id: "pikachu", name: "Pikachu", category: "Pokémon · original scene", src: "assets/character-scenes/pikachu-scene.png" },
    { id: "bulbasaur", name: "Bulbasaur", category: "Pokémon · original scene", src: "assets/character-scenes/bulbasaur-scene.png" },
    { id: "iron-man", name: "Iron Man", category: "Marvel · original scene", src: "assets/character-scenes/iron-man-scene.png" },
    { id: "spider-man", name: "Spider-Man", category: "Marvel · original scene", src: "assets/character-scenes/spider-man-scene.png" },
    { id: "harry-potter", name: "Harry Potter", category: "Wizarding world · original scene", src: "assets/character-scenes/harry-potter-scene.png" },
    { id: "hermione", name: "Hermione", category: "Wizarding world · original scene", src: "assets/character-scenes/hermione-scene.png" },
    // Preserve the original TRAVESÍA companions as additional choices.
    { id: "bloop", name: "Bloop", category: "TRAVESÍA original", src: "assets/companions/bloop-mini.svg" },
    { id: "sprout", name: "Sprout", category: "TRAVESÍA original", src: "assets/companions/sprout.webp" },
    { id: "pip", name: "Pip", category: "TRAVESÍA original", src: "assets/companions/pip.webp" },
    { id: "roo", name: "Roo", category: "TRAVESÍA original", src: "assets/companions/roo.webp" },
    { id: "mira", name: "Mira", category: "TRAVESÍA original", src: "assets/companions/mira.webp" },
    { id: "orbit", name: "Orbit", category: "TRAVESÍA original", src: "assets/companions/orbit.webp" },
    { id: "paws", name: "Paws", category: "TRAVESÍA original", src: "assets/companions/paws.webp" }
  ]);

  const byId = new Map(characters.map((character) => [character.id, character]));
  const defaultForIndex = (index) => characters[Math.max(0, Number(index) || 0) % characters.length].id;
  const get = (id) => byId.get(id) || characters[0];

  function normalize(people, stored) {
    const source = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    const used = new Set();
    const output = {};
    (Array.isArray(people) ? people : []).slice(0, 12).forEach((person, index) => {
      let chosen = typeof source[person] === "string" ? source[person] : "";
      if (!byId.has(chosen) || used.has(chosen)) {
        const preferred = defaultForIndex(index);
        chosen = !used.has(preferred) ? preferred : characters.find((item) => !used.has(item.id))?.id;
      }
      if (chosen) {
        output[person] = chosen;
        used.add(chosen);
      }
    });
    return output;
  }

  function available(people, selected, person) {
    const current = selected && typeof selected === "object" ? selected : {};
    const locked = new Set((Array.isArray(people) ? people : []).filter((name) => name !== person).map((name) => current[name]).filter(Boolean));
    return characters.filter((character) => !locked.has(character.id));
  }

  function assign(people, selected, person, characterId) {
    if (!Array.isArray(people) || !people.includes(person)) throw new Error("Choose a friend in this trip first.");
    if (!byId.has(characterId)) throw new Error("That character is not in the crew library.");
    const current = normalize(people, selected);
    const alreadyUsed = people.find((name) => name !== person && current[name] === characterId);
    if (alreadyUsed) throw new Error(`${get(characterId).name} is already assigned to ${alreadyUsed}.`);
    return { ...current, [person]: characterId };
  }

  const api = Object.freeze({ characters, get, defaultForIndex, normalize, available, assign });
  root.CityPulseFriendCharacters = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
