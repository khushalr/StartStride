const test = require("node:test");
const assert = require("node:assert/strict");
const logic = require("../logic.js");
const payload = require("../data.json");

test("fixture is explicitly synthetic and independently verifiable", () => {
  assert.equal(payload.meta.origin, "DEMO");
  assert.equal(payload.quality_rules.length, 16);
  assert.equal(logic.latestQuality(payload).passed, 13);
  assert.equal(logic.latestQuality(payload).failed, 3);
  assert.equal(logic.latestQuality(payload).affectedRuleRows, 4);
});

test("portfolio dashboard summarizes both routes and actions", () => {
  assert.deepEqual(logic.summary(payload), {
    events: 36, walk: 15, wait: 21, walkShare: 15 / 36,
    potentialSteps: 6930, verified: 0, catches: 0
  });
  assert.equal(logic.routeMix(payload).length, 3);
  assert.equal(logic.summary(payload, "510").events, 12);
  assert.equal(logic.summary(payload, "510").walk, 5);
  assert.equal(logic.hourlyActivity(payload).length, 3);
  assert.equal(logic.summary(payload, "999").events, 0);
});

test("walk decision requires positive verification", () => {
  const valid = {
    currentEta: 7, nextEta: 11, walking: 4, buffer: 2, feedAge: 0,
    wantsSteps: true, sameVehicle: true, nextStopServed: true,
    accessiblePath: true
  };
  assert.equal(logic.evaluateScenario(valid).action, "WALK");
  for (const key of ["sameVehicle", "nextStopServed", "accessiblePath", "wantsSteps"]) {
    assert.equal(logic.evaluateScenario({...valid, [key]: false}).action, "WAIT");
  }
  assert.equal(logic.evaluateScenario({...valid, feedAge: 91}).action, "WAIT");
  assert.equal(logic.evaluateScenario({...valid, nextEta: 6}).action, "WAIT");
  assert.equal(logic.evaluateScenario({...valid, currentEta: 4}).action, "WAIT");
  assert.equal(logic.evaluateScenario({...valid, walking: -1}).action, "WAIT");
  assert.equal(logic.evaluateScenario({...valid, nextEta: NaN}).action, "WAIT");
});
