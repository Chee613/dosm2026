const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, "dashboard", "data.js"), "utf8"), context);
const data = context.window.REEFSAFE_DATA;
const chat = require("../dashboard/chat.js");
const { answerQuestion } = chat;

test("redirects travel-safety questions to screening evidence", () => {
  const answer = answerQuestion("Is Redang safe to go?", data);

  assert.match(answer.text, /does not classify.*safe or unsafe/i);
  assert.match(answer.text, /Redang/);
  assert.equal(answer.island, "Redang");
  assert.equal(answer.pose, "warn");
});

test("uses the selected island when the question omits its name", () => {
  const answer = answerQuestion("How is this reef doing?", data, "Redang");

  assert.match(answer.text, /Redang/);
  assert.match(answer.text, /44\.8%/);
  assert.match(answer.text, /\+0\.65 pp\/yr/);
});

test("matches island names without case sensitivity", () => {
  const answer = answerQuestion("tell me about kapalai", data);

  assert.equal(answer.island, "Kapalai");
  assert.match(answer.text, /\+1\.65 pp\/yr/);
  assert.equal(answer.pose, "happy");
});

test("compares two named monitoring units", () => {
  const answer = answerQuestion("Compare Redang and Kapalai", data);

  assert.match(answer.text, /Redang.*[\+]0\.65 pp\/yr/);
  assert.match(answer.text, /Kapalai.*[\+]1\.65 pp\/yr/);
  assert.match(answer.text, /not a safety rating/i);
});

test("recommends only the verified visitor destination", () => {
  const answer = answerQuestion("Suggest a greener alternative", data);

  assert.match(answer.text, /Kapalai/);
  assert.doesNotMatch(answer.text, /Malacca/);
});

test("grounds model-selection answers in current metrics", () => {
  const answer = answerQuestion("Why Gradient Boosting?", data);

  assert.match(answer.text, /0\.380/);
  assert.match(answer.text, /83\.5%/);
  assert.match(answer.text, /screening/i);
});

test("technical questions outrank remembered island context", () => {
  const answer = answerQuestion("Why Gradient Boosting?", data, "Redang");

  assert.equal(answer.title, "Why Gradient Boosting?");
  assert.match(answer.text, /0\.380/);
  assert.doesNotMatch(answer.text, /Redang is in/);
});

test("answers general methodology questions with organised sections", () => {
  const answer = answerQuestion("What is the methodology?", data, "Redang");

  assert.equal(answer.title, "Methodology");
  assert.deepEqual(answer.sections.map((section) => section.label), ["Approach", "Validation", "Important limit"]);
  assert.match(answer.text, /expanding-window/i);
  assert.match(answer.text, /screening/i);
});

test("returns trusted provenance links for dataset source requests", () => {
  const answer = answerQuestion("Give me the dataset links", data, "Redang");

  assert.equal(answer.title, "Dataset sources");
  assert.ok(answer.links.length >= 3);
  assert.ok(answer.links.some((link) => link.href === "https://reefcheck.org.my/annualsurveyreports/"));
  assert.ok(answer.links.every((link) => link.href.startsWith("https://")));
});

test("explains the source of Reef-Adjacent Economy Potential", () => {
  const answer = answerQuestion("Where is the data Reef-Adjacent Economy Potential economy data from?", data, "Redang");

  assert.equal(answer.title, "Reef-Adjacent Economy Potential source");
  assert.match(answer.text, /Department of Marine Park Malaysia/i);
  assert.match(answer.text, /2011[–-]2015/);
  assert.match(answer.text, /RM8\.7 billion/);
  assert.match(answer.text, /not current revenue/i);
  assert.equal(answer.links.length, 1);
  assert.match(answer.links[0].href, /TOTAL%20ECONOMIC%20VALUE/);
});

test("uses an LLM classification to answer a misspelled priority question", async () => {
  const answer = await chat.resolveQuestion(
    "which island have the highest rosk rightnow",
    data,
    "Redang",
    async () => ({ intent: "highest_priority", islands: [], confidence: 0.98 }),
  );

  assert.equal(answer.title, "Highest screening priority");
  assert.match(answer.text, /Rhu/);
  assert.match(answer.text, /−3\.40 pp\/yr/);
  assert.match(answer.text, /not.*visitor-safety/i);
});

test("maps visit recommendations to a structured greener alternative", () => {
  const answer = chat.answerFromIntent(
    { intent: "greener_alternative", islands: [], confidence: 0.95 },
    "which plcae is good too visit",
    data,
    "Redang",
  );

  assert.equal(answer.title, "Greener monitored alternative");
  assert.match(answer.text, /Kapalai/);
  assert.deepEqual(answer.sections.map((section) => section.label), ["Suggestion", "Dashboard signal", "Important limit"]);
});

test("locally recognises a correctly spelled visit recommendation", () => {
  const answer = answerQuestion("Which place is good to visit?", data);

  assert.equal(answer.title, "Greener monitored alternative");
  assert.match(answer.text, /Kapalai/);
});

test("dashboard explanations are always structured", () => {
  const answer = answerQuestion("Explain this dashboard", data);

  assert.equal(answer.title, "ReefSafe dashboard");
  assert.deepEqual(answer.sections.map((section) => section.label), ["Purpose", "Colours", "Important limit"]);
});

test("falls back to local routing when the LLM is unavailable", async () => {
  const answer = await chat.resolveQuestion(
    "Why Gradient Boosting?",
    data,
    "Redang",
    async () => { throw new Error("offline"); },
  );

  assert.equal(answer.title, "Why Gradient Boosting?");
  assert.match(answer.text, /0\.380/);
});

test("island answers expose simple labelled sections", () => {
  const answer = answerQuestion("How is Redang doing?", data);

  assert.equal(answer.title, "Redang overview");
  assert.deepEqual(answer.sections.map((section) => section.label), ["Status", "Model signal", "What to check", "Important limit"]);
  assert.match(answer.sections[2].text, /\.$/);
});

test("refuses to invent current promotions", () => {
  const answer = answerQuestion("What government promotion can I book?", data);

  assert.match(answer.text, /no verified live promotion data/i);
  assert.match(answer.text, /official source/i);
});

test("returns a useful fallback and preserves input as plain text", () => {
  const question = "Write me a <script>alert(1)</script> poem";
  const answer = answerQuestion(question, data);

  assert.match(answer.text, /I can help with/i);
  assert.doesNotMatch(answer.text, /<script>/i);
});

test("dashboard ships the accessible copilot interface and avatar set", () => {
  const html = fs.readFileSync(path.join(root, "dashboard", "index.html"), "utf8");

  assert.match(html, /id="reef-chat-launcher"[^>]*aria-controls="reef-chat-panel"/);
  assert.match(html, /id="reef-chat-panel"[^>]*role="dialog"/);
  assert.match(html, /id="reef-chat-messages"[^>]*role="log"/);
  assert.match(html, /<label[^>]*for="reef-chat-input"/);
  assert.match(html, /<script src="chat\.js(?:\?v=[^"]*)?"><\/script>/);
  assert.equal(typeof chat.initChat, "function");

  for (const pose of ["idle", "wave", "think", "answer", "happy", "warn"]) {
    assert.equal(
      fs.existsSync(path.join(root, "dashboard", "assets", "avatar", `avatar_${pose}.png`)),
      true,
      `missing ${pose} avatar`,
    );
  }
});
