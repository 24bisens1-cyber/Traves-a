/* Pure, testable Split Expenses calculations. Amounts are stored as integer paise. */
(function attachExpenseLedger(root, factory) {
  const api = factory();
  if (root) root.CityPulseExpenseLedger = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : null, function createExpenseLedgerApi() {
  "use strict";
  const MAX_PEOPLE = 12;
  const MAX_AMOUNT_PAISE = 10_000_000_000;

  function normalizePeople(people) {
    if (!Array.isArray(people)) throw new TypeError("People must be an array.");
    const names = people.map((value) => String(value ?? "").trim());
    if (names.length < 1 || names.length > MAX_PEOPLE) throw new RangeError(`A trip must have between 1 and ${MAX_PEOPLE} people.`);
    if (names.some((name) => !name || name.length > 60)) throw new TypeError("Friend names must contain 1–60 characters.");
    if (new Set(names.map((name) => name.toLocaleLowerCase())).size !== names.length) throw new TypeError("Friend names must be unique.");
    return names;
  }

  function toPaise(amount) {
    const value = Number(amount);
    if (!Number.isFinite(value) || value <= 0 || value * 100 > MAX_AMOUNT_PAISE) throw new RangeError("Expense amount must be positive and within the supported limit.");
    return Math.round(value * 100);
  }

  function calculate(peopleInput, expensesInput) {
    const people = normalizePeople(peopleInput);
    if (!Array.isArray(expensesInput)) throw new TypeError("Expenses must be an array.");
    const eligible = new Set(people);
    const paidPaise = Object.fromEntries(people.map((name) => [name, 0]));
    const owedPaise = Object.fromEntries(people.map((name) => [name, 0]));
    let totalPaise = 0;

    for (const [index, expense] of expensesInput.entries()) {
      if (!expense || typeof expense !== "object" || Array.isArray(expense)) throw new TypeError(`Expense ${index + 1} must be an object.`);
      const amountPaise = Math.round(Number(expense.amount) * 100);
      if (!Number.isSafeInteger(amountPaise) || amountPaise <= 0 || amountPaise > MAX_AMOUNT_PAISE) throw new RangeError(`Expense ${index + 1} must have a positive amount within the supported limit.`);
      if (!eligible.has(expense.paidBy)) throw new TypeError(`Expense ${index + 1} has a payer who is not in this trip.`);
      const rawParticipants = Array.isArray(expense.splitWith) ? expense.splitWith : people;
      if (rawParticipants.some((name) => !eligible.has(name))) throw new TypeError(`Expense ${index + 1} includes a participant who is not in this trip.`);
      const participants = [...new Set(rawParticipants)];
      if (!participants.length) throw new TypeError(`Expense ${index + 1} must be shared by at least one person.`);
      totalPaise += amountPaise;
      paidPaise[expense.paidBy] += amountPaise;
      const base = Math.floor(amountPaise / participants.length);
      const remainder = amountPaise % participants.length;
      participants.forEach((name, participantIndex) => { owedPaise[name] += base + (participantIndex < remainder ? 1 : 0); });
    }

    const balancePaise = Object.fromEntries(people.map((name) => [name, (paidPaise[name] || 0) - (owedPaise[name] || 0)]));
    const creditors = people.map((name) => ({ name, amount: balancePaise[name] })).filter((row) => row.amount > 0);
    const debtors = people.map((name) => ({ name, amount: -balancePaise[name] })).filter((row) => row.amount > 0);
    const transfers = [];
    let debtorIndex = 0, creditorIndex = 0;
    while (debtorIndex < debtors.length && creditorIndex < creditors.length) {
      const amount = Math.min(debtors[debtorIndex].amount, creditors[creditorIndex].amount);
      if (amount > 0) transfers.push({ from: debtors[debtorIndex].name, to: creditors[creditorIndex].name, amount });
      debtors[debtorIndex].amount -= amount;
      creditors[creditorIndex].amount -= amount;
      if (debtors[debtorIndex].amount === 0) debtorIndex++;
      if (creditors[creditorIndex].amount === 0) creditorIndex++;
    }

    return {
      people,
      totalPaise,
      equalSharePaise: Math.round(totalPaise / people.length),
      paidPaise,
      owedPaise,
      balancePaise,
      summary: people.map((name) => ({ name, paid: paidPaise[name] || 0, share: owedPaise[name] || 0, balance: balancePaise[name] || 0 })),
      transfers,
      reconciles: Object.values(balancePaise).reduce((sum, balance) => sum + balance, 0) === 0,
    };
  }

  function createNextMemberName(peopleInput) {
    const people = normalizePeople(peopleInput);
    if (people.length >= MAX_PEOPLE) return null;
    let number = people.length + 1;
    let name = `Friend ${number}`;
    const existing = new Set(people.map((person) => person.toLocaleLowerCase()));
    while (existing.has(name.toLocaleLowerCase())) { number++; name = `Friend ${number}`; }
    return name;
  }

  function removeMember(peopleInput, expensesInput, removedName, payerReplacement = null) {
    const people = normalizePeople(peopleInput);
    if (!people.includes(removedName)) throw new Error("Friend is not in this trip.");
    if (people.length <= 1) throw new RangeError("Keep at least one person in the trip.");
    const remaining = people.filter((name) => name !== removedName);
    const paidExpenses = (Array.isArray(expensesInput) ? expensesInput : []).filter((expense) => expense?.paidBy === removedName);
    if (paidExpenses.length && !remaining.includes(payerReplacement)) throw new Error("Reassign this friend's paid expenses to a remaining member before removing them.");
    const expenses = (Array.isArray(expensesInput) ? expensesInput : []).map((expense) => {
      let splitWith = (Array.isArray(expense.splitWith) ? expense.splitWith : people).filter((name) => name !== removedName && remaining.includes(name));
      if (!splitWith.length) splitWith = [...remaining];
      return { ...expense, paidBy: expense.paidBy === removedName ? payerReplacement : expense.paidBy, splitWith };
    });
    return { people: remaining, expenses };
  }

  return Object.freeze({ MAX_PEOPLE, normalizePeople, toPaise, calculate, createNextMemberName, removeMember });
});
