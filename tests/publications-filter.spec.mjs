// Smoke test: verifies the /publications/ filter checkboxes actually
// reduce the visible publications list.
//
//   node tests/publications-filter.spec.mjs
//
// Assumes `astro preview` (or any static server) is serving the built
// site on http://127.0.0.1:4321/. Boot it yourself first:
//   npm run build && npx astro preview --port 4321 &
import { chromium } from "playwright";

const BASE = process.env.BASE_URL ?? "http://127.0.0.1:4321";

function pass(msg) {
  console.log(`  ✓ ${msg}`);
}
function fail(msg) {
  console.error(`  ✗ ${msg}`);
  process.exitCode = 1;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console.error: ${m.text()}`);
  });

  await page.goto(`${BASE}/publications/`, { waitUntil: "networkidle" });
  console.log("loaded /publications/");

  // Baseline: total + visible counts.
  const total = await page.locator("[data-pub]").count();
  const initiallyVisible = await page.evaluate(
    () => Array.from(document.querySelectorAll("[data-pub]")).filter((el) => el.style.display !== "none").length,
  );
  console.log(`  total items: ${total}, initially visible: ${initiallyVisible}`);
  total > 100 ? pass("at least 100 publications rendered") : fail(`only ${total} publications rendered`);
  initiallyVisible === total
    ? pass("all items visible with no filter")
    : fail(`expected all ${total} visible, got ${initiallyVisible}`);

  // ---- Toggle YEAR=2024 ----
  await page.locator('fieldset[data-filter-group="year"] input[type=checkbox][value="2024"]').check();
  await page.waitForTimeout(50);
  const expectedYear = await page.evaluate(
    () => document.querySelectorAll('[data-pub][data-year="2024"]').length,
  );
  const visibleAfterYear = await page.evaluate(
    () => Array.from(document.querySelectorAll("[data-pub]")).filter((el) => el.style.display !== "none").length,
  );
  const counterAfterYear = (await page.locator("[data-pub-count]").textContent())?.trim();
  console.log(`  year=2024 → expected ${expectedYear}, visible ${visibleAfterYear}, counter ${counterAfterYear}`);
  visibleAfterYear === expectedYear
    ? pass(`year filter reduces to ${expectedYear} items`)
    : fail(`year filter broken: ${visibleAfterYear} visible vs expected ${expectedYear}`);
  String(counterAfterYear) === String(expectedYear)
    ? pass("counter matches filtered count")
    : fail(`counter mismatch: ${counterAfterYear} != ${expectedYear}`);

  // ---- Add TYPE=preprint (AND across columns) ----
  await page.locator('fieldset[data-filter-group="type"] input[type=checkbox][value="preprint"]').check();
  await page.waitForTimeout(50);
  const expectedYearAndType = await page.evaluate(
    () => document.querySelectorAll('[data-pub][data-year="2024"][data-type="preprint"]').length,
  );
  const visibleAfterAnd = await page.evaluate(
    () => Array.from(document.querySelectorAll("[data-pub]")).filter((el) => el.style.display !== "none").length,
  );
  console.log(`  year=2024 AND type=preprint → expected ${expectedYearAndType}, visible ${visibleAfterAnd}`);
  visibleAfterAnd === expectedYearAndType
    ? pass("AND across columns works")
    : fail(`AND across columns broken: ${visibleAfterAnd} visible vs expected ${expectedYearAndType}`);

  // ---- Add YEAR=2023 (OR within year column) ----
  await page.locator('fieldset[data-filter-group="year"] input[type=checkbox][value="2023"]').check();
  await page.waitForTimeout(50);
  const expectedOrAnd = await page.evaluate(() => {
    return Array.from(document.querySelectorAll("[data-pub]")).filter((el) => {
      const y = el.dataset.year;
      return (y === "2024" || y === "2023") && el.dataset.type === "preprint";
    }).length;
  });
  const visibleAfterOrAnd = await page.evaluate(
    () => Array.from(document.querySelectorAll("[data-pub]")).filter((el) => el.style.display !== "none").length,
  );
  console.log(`  (year=2024 OR 2023) AND type=preprint → expected ${expectedOrAnd}, visible ${visibleAfterOrAnd}`);
  visibleAfterOrAnd === expectedOrAnd
    ? pass("OR within column works")
    : fail(`OR within column broken: ${visibleAfterOrAnd} visible vs expected ${expectedOrAnd}`);

  // ---- Reset ----
  await page.locator("[data-reset]").click();
  await page.waitForTimeout(50);
  const afterReset = await page.evaluate(
    () => Array.from(document.querySelectorAll("[data-pub]")).filter((el) => el.style.display !== "none").length,
  );
  afterReset === total
    ? pass("reset restores all items")
    : fail(`reset broken: ${afterReset} visible vs ${total} total`);

  if (errors.length) {
    console.error("\nUncaught JS errors during run:");
    errors.forEach((e) => console.error(" ", e));
    process.exitCode = 1;
  }
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
