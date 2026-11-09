const test = require('node:test');
const assert = require('node:assert/strict');
const ledger = require('../expense-ledger.js');

test('equal group split calculates paise-accurate balances and settlement', () => {
  const people = ['Asha', 'Bina', 'Charu', 'Diya'];
  const result = ledger.calculate(people, [{ amount: 1000, paidBy: 'Asha', splitWith: people }]);
  assert.equal(result.totalPaise, 100000);
  assert.equal(result.equalSharePaise, 25000);
  assert.deepEqual(result.balancePaise, { Asha: 75000, Bina: -25000, Charu: -25000, Diya: -25000 });
  assert.equal(result.transfers.length, 3);
  assert.equal(result.transfers.reduce((sum, transfer) => sum + transfer.amount, 0), 75000);
  assert.equal(result.reconciles, true);
});

test('odd paise remainder is distributed deterministically', () => {
  const people = ['A', 'B', 'C', 'D', 'E'];
  const result = ledger.calculate(people, [{ amount: 1000.01, paidBy: 'A', splitWith: people }]);
  assert.deepEqual(people.map((person) => result.owedPaise[person]), [20001, 20000, 20000, 20000, 20000]);
  assert.equal(Object.values(result.balancePaise).reduce((sum, value) => sum + value, 0), 0);
});

test('custom participants exclude people outside the expense', () => {
  const result = ledger.calculate(['A', 'B', 'C'], [{ amount: 901.01, paidBy: 'B', splitWith: ['A', 'B'] }]);
  assert.equal(result.owedPaise.A, 45051);
  assert.equal(result.owedPaise.B, 45050);
  assert.equal(result.owedPaise.C, 0);
  assert.equal(result.balancePaise.C, 0);
  assert.equal(result.reconciles, true);
});

test('member names can grow to twelve and handle deleted-number gaps', () => {
  assert.equal(ledger.createNextMemberName(['Friend 1', 'Friend 2', 'Friend 4']), 'Friend 5');
  assert.equal(ledger.createNextMemberName(Array.from({ length: 12 }, (_, i) => `Friend ${i + 1}`)), null);
});

test('removing a participant recalculates splits but keeps prior paid amount', () => {
  const people = ['A', 'B', 'C'];
  const expenses = [{ id: '1', amount: 900, paidBy: 'A', splitWith: [...people] }];
  const result = ledger.removeMember(people, expenses, 'C');
  assert.deepEqual(result.people, ['A', 'B']);
  assert.deepEqual(result.expenses[0].splitWith, ['A', 'B']);
  const after = ledger.calculate(result.people, result.expenses);
  assert.deepEqual(after.balancePaise, { A: 45000, B: -45000 });
  assert.equal(after.reconciles, true);
});

test('removing a payer requires explicit reassignment and then reconciles', () => {
  const people = ['A', 'B', 'C'];
  const expenses = [{ id: '1', amount: 600, paidBy: 'B', splitWith: [...people] }];
  assert.throws(() => ledger.removeMember(people, expenses, 'B'), /Reassign/);
  const result = ledger.removeMember(people, expenses, 'B', 'A');
  assert.equal(result.expenses[0].paidBy, 'A');
  assert.deepEqual(result.expenses[0].splitWith, ['A', 'C']);
  assert.equal(ledger.calculate(result.people, result.expenses).reconciles, true);
});

test('rejects duplicate names and keeps at least one member', () => {
  assert.throws(() => ledger.calculate(['A', 'a'], []), /unique/);
  assert.throws(() => ledger.removeMember(['Only'], [], 'Only'), /at least one/);
});

test('rejects expenses with invalid payers, participants, and amounts', () => {
  assert.throws(() => ledger.calculate(['A', 'B'], [{ amount: 10, paidBy: 'Nobody', splitWith: ['A', 'B'] }]), /payer/);
  assert.throws(() => ledger.calculate(['A', 'B'], [{ amount: 10, paidBy: 'A', splitWith: ['A', 'Nobody'] }]), /participant/);
  assert.throws(() => ledger.calculate(['A', 'B'], [{ amount: 0, paidBy: 'A', splitWith: ['A', 'B'] }]), /positive amount/);
  assert.throws(() => ledger.calculate(['A', 'B'], [{ amount: 100000001, paidBy: 'A', splitWith: ['A', 'B'] }]), /supported limit/);
});
